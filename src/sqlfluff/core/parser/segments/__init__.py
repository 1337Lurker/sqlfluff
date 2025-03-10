"""Definitions of the segment classes."""

# flake8: noqa: F401

from sqlfluff.core.parser.segments.base import (
    BaseSegment,
    BaseFileSegment,
    UnparsableSegment,
    BracketedSegment,
)
from sqlfluff.core.parser.segments.generator import SegmentGenerator
from sqlfluff.core.parser.segments.raw import (
    RawSegment,
    CodeSegment,
    UnlexableSegment,
    CommentSegment,
    WhitespaceSegment,
    NewlineSegment,
    KeywordSegment,
    SymbolSegment,
)
from sqlfluff.core.parser.segments.ephemeral import EphemeralSegment, allow_ephemeral
from sqlfluff.core.parser.segments.meta import (
    MetaSegment,
    Indent,
    Dedent,
    TemplateSegment,
)
