CREATE TABLE myschema.t1
(   a VARCHAR(20) UTF8,
    b DECIMAL(24,4) NOT NULL COMMENT IS 'The B column',
    c DECIMAL DEFAULT 122,
    d DOUBLE,
    e TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    f BOOL);
CREATE TABLE "MYSCHEMA"."T2" AS (SELECT * FROM t1) WITH NO DATA;
CREATE OR REPLACE TABLE "MYSCHEMA".T2 AS SELECT a,b,c+1 AS c FROM t1;
CREATE TABLE t3 AS (SELECT count(*) AS my_count FROM t1) WITH NO DATA;
CREATE TABLE t4 LIKE t1;
CREATE TABLE t5 (   id int IDENTITY PRIMARY KEY DISABLE,
                    LIKE t1 INCLUDING DEFAULTS,
                    g DOUBLE,
                    DISTRIBUTE BY a,b
                    );
CREATE TABLE t6 (   order_id INT,
                    order_price DOUBLE,
                    order_date DATE,
                    country VARCHAR(40),
                    CONSTRAINT t6_pk PRIMARY KEY (order_id),
                    DISTRIBUTE BY order_id, PARTITION BY order_date)
COMMENT IS 'a great table';
CREATE OR REPLACE TABLE t8 (ref_id int CONSTRAINT FK_T5 REFERENCES t5 (id) DISABLE, b VARCHAR(20));
