"""The Redshift dialect."""

from sqlfluff.core.parser import (
    OneOf,
    AnyNumberOf,
    Ref,
    Sequence,
    Bracketed,
    OptionallyBracketed,
    Anything,
    BaseSegment,
    Delimited,
    RegexLexer,
    StringParser,
    CodeSegment,
    NamedParser,
    SymbolSegment,
    KeywordSegment,
    StartsWith,
    CommentSegment,
)

from sqlfluff.core.dialects import load_raw_dialect
from sqlfluff.dialects.redshift_keywords import RESERVED_KEYWORDS, UNRESERVED_KEYWORDS

postgres_dialect = load_raw_dialect("postgres")

redshift_dialect = postgres_dialect.copy_as("redshift")

redshift_dialect.sets("reserved_keywords").update(RESERVED_KEYWORDS)
redshift_dialect.sets("unreserved_keywords").update(UNRESERVED_KEYWORDS)

redshift_dialect.add(
    EncodeGrammar=Sequence("ENCODE", OneOf("AZ64", "BYTEDICT", "DELTA", "DELTA32K", "LZO", "MOSTLY8", "MOSTLY16", "MOSTLY32", "RUNLENGTH", "TEXT255", "TEXT32K", "ZSTD"))
)

@redshift_dialect.segment(replace=True)
class CreateTableStatementSegment(BaseSegment):
    """A `CREATE TABLE` statement.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_SELECT_synopsis.html
    """

    type = "create_table_statement"

    match_grammar = Sequence(
        "CREATE",
        OneOf(
            Sequence(
                OneOf("LOCAL", optional=True),
                Ref("TemporaryGrammar", optional=True),
            ),
            optional=True,
        ),
        "TABLE",
        Ref("IfNotExistsGrammar", optional=True),
        Ref("TableReferenceSegment"),
        OneOf(
            # Columns and comment syntax:
            Sequence(
                Bracketed(
                    Delimited(
                        OneOf(
                            Sequence(
                                Ref("ColumnReferenceSegment"),
                                Ref("DatatypeSegment"),
                                Sequence(
                                    "COLLATE",
                                    Ref("QuotedLiteralSegment"),
                                    optional=True,
                                ),
                                AnyNumberOf(
                                    Ref("ColumnConstraintSegment", optional=True)
                                ),
                            ),
                            Ref("TableConstraintSegment"),
                            Sequence(
                                "LIKE",
                                Ref("TableReferenceSegment"),
                                AnyNumberOf(Ref("LikeOptionSegment"), optional=True),
                            ),
                        ),
                    )
                ),
                Sequence(
                    "INHERITS",
                    Bracketed(
                        Delimited(
                            Ref("TableReferenceSegment"), delimiter=Ref("CommaSegment")
                        )
                    ),
                    optional=True,
                ),
            ),
            # Create OF syntax:
            Sequence(
                "OF",
                Ref("ParameterNameSegment"),
                Bracketed(
                    Delimited(
                        Sequence(
                            Ref("ColumnReferenceSegment"),
                            Sequence("WITH", "OPTIONS", optional=True),
                            AnyNumberOf(Ref("ColumnConstraintSegment")),
                        ),
                        Ref("TableConstraintSegment"),
                        delimiter=Ref("CommaSegment"),
                    ),
                    optional=True,
                ),
            ),
            # Create PARTITION OF syntax
            Sequence(
                "PARTITION",
                "OF",
                Ref("TableReferenceSegment"),
                Bracketed(
                    Delimited(
                        Sequence(
                            Ref("ColumnReferenceSegment"),
                            Sequence("WITH", "OPTIONS", optional=True),
                            AnyNumberOf(Ref("ColumnConstraintSegment")),
                        ),
                        Ref("TableConstraintSegment"),
                        delimiter=Ref("CommaSegment"),
                    ),
                    optional=True,
                ),
                OneOf(
                    Sequence("FOR", "VALUES", Ref("PartitionBoundSpecSegment")),
                    "DEFAULT",
                ),
            ),
        ),
        AnyNumberOf(
            Sequence(
                "DISTSTYLE",
                OneOf("AUTO", "EVEN", "KEY", "ALL"),
            ),
            Sequence(
                "DISTKEY",
                Ref("BracketedColumnReferenceListGrammar"),
            ),
            Sequence(
                "SORTKEY",
                Ref("BracketedColumnReferenceListGrammar"),
            ),
            Sequence(
                OneOf(
                    Sequence(AnyNumberOf(OneOf("COMPOUND", "INTERLEAVED")), "SORTKEY", Ref("BracketedColumnReferenceListGrammar")),
                )
            ),
        ),
    )

@redshift_dialect.segment(replace=True)
class ColumnConstraintSegment(BaseSegment):
    """A column option; each CREATE TABLE column can have 0 or more.
    """

    type = "column_constraint_segment"
    # Column constraint from
    # https://www.postgresql.org/docs/12/sql-createtable.html
    match_grammar = Sequence(
        Sequence(
            "CONSTRAINT",
            Ref("ObjectReferenceSegment"),  # Constraint name
            optional=True,
        ),
        OneOf(
            Sequence(Ref.keyword("NOT", optional=True), "NULL"),  # NOT NULL or NULL
            "UNIQUE",
            Ref("EncodeGrammar"),
            Ref("PrimaryKeyGrammar"),
            Sequence(  # REFERENCES reftable [ ( refcolumn) ]
                "REFERENCES",
                Ref("ColumnReferenceSegment"),
                # Foreign columns making up FOREIGN KEY constraint
                Ref("BracketedColumnReferenceListGrammar", optional=True),
            ),
        ),
    )

@redshift_dialect.segment(replace=True)
class TableConstraintSegment(BaseSegment):
    """A table constraint, e.g. for CREATE TABLE.
    """

    type = "table_constraint_segment"

    match_grammar = Sequence(
        Sequence(  # [ CONSTRAINT <Constraint name> ]
            "CONSTRAINT", Ref("ObjectReferenceSegment"), optional=True
        ),
        OneOf(
            Sequence(
                "CHECK",
                Bracketed(Ref("ExpressionSegment")),
                Sequence("NO", "INHERIT", optional=True),
            ),
            Sequence(  # UNIQUE ( column_name [, ... ] )
                "UNIQUE",
                Ref("BracketedColumnReferenceListGrammar"),
                Ref("IndexParametersSegment", optional=True),
            ),
            Sequence(  # PRIMARY KEY ( column_name [, ... ] ) index_parameters
                Ref("PrimaryKeyGrammar"),
                # Columns making up PRIMARY KEY constraint
                Ref("BracketedColumnReferenceListGrammar"),
                Ref("IndexParametersSegment", optional=True),
            ),
            Sequence(
                "EXCLUDE",
                Sequence("USING", Ref("FunctionSegment"), optional=True),
                Bracketed(
                    Delimited(
                        Sequence(
                            Ref("ExcludeElementSegment"),
                            "WITH",
                            Ref("ComparisonOperatorGrammar"),
                        )
                    )
                ),
                Ref("IndexParametersSegment", optional=True),
                Sequence("WHERE", Ref("ExpressionSegment")),
            ),
            Sequence(  # FOREIGN KEY ( column_name [, ... ] )
                # REFERENCES reftable [ ( refcolumn [, ... ] ) ]
                "FOREIGN",
                "KEY",
                # Local columns making up FOREIGN KEY constraint
                Ref("BracketedColumnReferenceListGrammar"),
                "REFERENCES",
                Ref("ColumnReferenceSegment"),
                # Foreign columns making up FOREIGN KEY constraint
                Ref("BracketedColumnReferenceListGrammar", optional=True),
                Sequence("MATCH", OneOf("FULL", "PARTIAL", "SIMPLE"), optional=True),
                Sequence(
                    "ON", "DELETE", Ref("ReferentialActionSegment"), optional=True
                ),
                Sequence(
                    "ON", "UPDATE", Ref("ReferentialActionSegment"), optional=True
                ),
            ),
        ),
    )