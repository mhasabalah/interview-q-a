---
title: Database
aliases: [Database, SQL]
tags: [database, sql, interview]
order: 6
---

# Database Interview Questions & Answers

> [!info]+ Related Notes
> [[07-Domain-Driven-Design|Domain-Driven Design]] · [[16-System-Design|System Design]] · [[18-Distributed-Systems-Reliability|Distributed Systems & Reliability]]

> [!tip] Going deeper
> **Replication lag and read-your-own-writes**, **connection pool exhaustion and PgBouncer**, and *when sharding is actually worth its pain* are covered in [[18-Distributed-Systems-Reliability#3. Scaling|Distributed Systems & Reliability]].

## Fundamental Concepts

### 1. What is a database?
A database is an organized collection of structured data stored electronically in a computer system. It's managed by a Database Management System (DBMS) that allows users to create, read, update, and delete data efficiently.

### 2. What is the difference between SQL and NoSQL databases?
- **SQL (Relational)**: Structured data with predefined schema, ACID compliance, uses tables with relationships, vertical scaling. Examples: MySQL, PostgreSQL, SQL Server.
- **NoSQL**: Flexible schema, horizontal scaling, various data models (document, key-value, graph, column-family). Examples: MongoDB, Redis, Cassandra, Neo4j.

### 3. What are the main types of NoSQL databases?
- **Document**: MongoDB, CouchDB (JSON-like documents)
- **Key-Value**: Redis, DynamoDB (simple key-value pairs)
- **Column-Family**: Cassandra, HBase (wide-column stores)
- **Graph**: Neo4j, ArangoDB (nodes and relationships)

### 4. What is ACID in databases?
- **Atomicity**: All operations in a transaction succeed or all fail
- **Consistency**: Database remains in valid state before and after transaction
- **Isolation**: Concurrent transactions don't interfere with each other
- **Durability**: Committed transactions are permanently saved

### 5. What is BASE in NoSQL databases?
- **Basically Available**: System guarantees availability
- **Soft state**: State may change over time without input
- **Eventual consistency**: System will become consistent over time

## Database Design

### 6. What is normalization?
Normalization is organizing database tables to reduce redundancy and dependency. It divides large tables into smaller ones and defines relationships between them.

**Normal Forms:**
- **1NF**: Atomic values, no repeating groups
- **2NF**: 1NF + no partial dependencies on composite keys
- **3NF**: 2NF + no transitive dependencies
- **BCNF**: Every determinant is a candidate key

### 7. What is denormalization and when would you use it?
Denormalization intentionally adds redundancy to improve read performance by reducing joins. Use it when:
- Read operations vastly outnumber writes
- Complex joins significantly impact performance
- Real-time query performance is critical
- Data warehousing and reporting systems

### 8. What is a primary key?
A primary key uniquely identifies each record in a table. It must contain unique values and cannot contain NULL. A table can have only one primary key.

### 9. What is a foreign key?
A foreign key is a field that references the primary key of another table, establishing relationships between tables and maintaining referential integrity.

### 10. What is an index and why is it important?
An index is a data structure that improves query performance by allowing faster data retrieval. It works like a book index, pointing to data locations without scanning entire tables.

**Types:**
- Clustered: Determines physical order of data
- Non-clustered: Separate structure pointing to data
- Unique: Ensures uniqueness
- Composite: Index on multiple columns

## Querying

### 11. Explain the difference between WHERE and HAVING clauses
- **WHERE**: Filters rows before grouping, cannot use aggregate functions
- **HAVING**: Filters groups after GROUP BY, can use aggregate functions

```sql
SELECT department, AVG(salary)
FROM employees
WHERE status = 'active'
GROUP BY department
HAVING AVG(salary) > 50000;
```

### 12. What is the difference between INNER JOIN and OUTER JOIN?
- **INNER JOIN**: Returns only matching rows from both tables
- **LEFT OUTER JOIN**: All rows from left table + matching from right
- **RIGHT OUTER JOIN**: All rows from right table + matching from left
- **FULL OUTER JOIN**: All rows from both tables

### 13. What are aggregate functions?
Functions that perform calculations on multiple rows and return a single value:
- **COUNT()**: Number of rows
- **SUM()**: Total of numeric column
- **AVG()**: Average value
- **MIN()/MAX()**: Minimum/Maximum value

### 14. What is a subquery?
A query nested inside another query. Can be used in SELECT, FROM, WHERE, or HAVING clauses.

```sql
SELECT name FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

### 15. What is the difference between DELETE, TRUNCATE, and DROP?
- **DELETE**: Removes rows, can use WHERE, can rollback, triggers fire, slower
- **TRUNCATE**: Removes all rows, faster, cannot rollback, no triggers, resets identity
- **DROP**: Removes entire table structure and data permanently

## Performance & Optimization

### 16. What is query optimization?
Process of improving query performance through:
- Proper indexing
- Query rewriting
- Avoiding SELECT *
- Using appropriate JOIN types
- Limiting result sets
- Analyzing execution plans

### 17. What is database sharding?
Horizontal partitioning that distributes data across multiple databases or servers. Each shard contains a subset of data, improving scalability and performance.

### 18. What is database replication?
Copying data from one database to others to ensure:
- High availability
- Load balancing
- Disaster recovery
- Geographic distribution

**Types:** Master-Slave, Master-Master, Multi-Master

### 19. What is connection pooling?
Maintaining a cache of database connections that can be reused, reducing the overhead of creating new connections for each request.

### 20. What is a execution plan?
A roadmap showing how the database engine will execute a query. It helps identify performance bottlenecks and optimization opportunities.

## Transactions

### 21. What is a transaction?
A logical unit of work containing one or more operations that must all succeed or all fail together. Ensures data integrity.

### 22. What are transaction isolation levels?
- **Read Uncommitted**: Lowest isolation, dirty reads possible
- **Read Committed**: Prevents dirty reads
- **Repeatable Read**: Prevents dirty and non-repeatable reads
- **Serializable**: Highest isolation, prevents phantom reads

### 23. What is a deadlock?
Occurs when two or more transactions wait for each other to release locks, causing a circular dependency. DBMS typically detects and resolves by rolling back one transaction.

### 24. What is optimistic vs pessimistic locking?
- **Pessimistic**: Locks data when transaction starts, prevents conflicts
- **Optimistic**: No locks, checks for conflicts at commit time using version numbers

## Advanced Topics

### 25. What is a stored procedure?
Precompiled SQL code stored in the database that can be executed repeatedly. Benefits include:
- Improved performance
- Code reusability
- Security (grant execute permissions)
- Reduced network traffic

### 26. What is a view?
A virtual table based on a SQL query. Doesn't store data but provides a way to:
- Simplify complex queries
- Restrict data access
- Present data differently

### 27. What is a trigger?
Automatically executed code in response to specific events (INSERT, UPDATE, DELETE) on a table. Used for:
- Enforcing business rules
- Auditing changes
- Maintaining derived data

### 28. What is the CAP theorem?
A distributed database can guarantee only 2 of 3:
- **Consistency**: All nodes see same data
- **Availability**: System always responds
- **Partition Tolerance**: System works despite network failures

### 29. What is database partitioning?
Dividing large tables into smaller pieces for better performance:
- **Horizontal**: Splitting rows across tables
- **Vertical**: Splitting columns across tables
- **Range**: Based on value ranges
- **List**: Based on specific values
- **Hash**: Based on hash function

### 30. What is a cursor?
A database object for traversing result sets row-by-row. Generally avoided in favor of set-based operations due to performance overhead.

## NoSQL Specific

### 31. What is eventual consistency?
A consistency model where updates to a database will eventually propagate to all nodes, but there may be temporary inconsistencies.

### 32. What is a document database?
Stores data as documents (usually JSON/BSON) where each document is self-contained and can have a different structure. Example: MongoDB.

### 33. What is denormalization in NoSQL?
Embedding related data together in a single document/record to optimize read operations, accepting data duplication.

### 34. When would you choose NoSQL over SQL?
- Massive scale (horizontal scaling needed)
- Flexible/dynamic schema requirements
- High write throughput
- Unstructured or semi-structured data
- Real-time applications
- Distributed architecture

## Security

### 35. What is SQL injection?
A security vulnerability where malicious SQL code is inserted into application queries. Prevention:
- Use parameterized queries/prepared statements
- Input validation and sanitization
- Principle of least privilege
- Use ORMs properly

### 36. What are database roles and permissions?
- **Roles**: Groups of privileges assigned to users
- **Permissions**: Grant/revoke access to database objects (SELECT, INSERT, UPDATE, DELETE, EXECUTE)
- Implements principle of least privilege

### 37. What is encryption at rest vs in transit?
- **At Rest**: Encrypts stored data on disk
- **In Transit**: Encrypts data moving between client and server (TLS/SSL)

## Modern Database Concepts

### 38. What is a time-series database?
Optimized for handling time-stamped data. Examples: InfluxDB, TimescaleDB. Used for:
- IoT sensor data
- Metrics and monitoring
- Financial data

### 39. What is database versioning/migration?
Managing database schema changes over time through version-controlled scripts. Tools: Flyway, Liquibase, Entity Framework Migrations.

### 40. What is database backup and recovery?
**Strategies:**
- Full backup: Complete database copy
- Incremental: Only changed data since last backup
- Differential: Changes since last full backup
- Point-in-time recovery: Restore to specific moment

**Recovery Models:**
- Simple: Minimal logging
- Full: Complete transaction logging
- Bulk-logged: Optimized for bulk operations

## Advanced Querying

### 41. What are window functions?
Functions that perform calculations across a set of rows related to the current row, without collapsing them into a single result (unlike aggregates + GROUP BY).

```sql
SELECT
    name,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rank_in_dept,
    RANK()       OVER (PARTITION BY department ORDER BY salary DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rank_no_gaps
FROM employees;
```
- **ROW_NUMBER()**: Unique sequential number, no ties
- **RANK()**: Same rank for ties, skips next rank(s)
- **DENSE_RANK()**: Same rank for ties, no gaps

### 42. What is a CTE (Common Table Expression)?
A named temporary result set defined with `WITH`, scoped to a single query. Improves readability and enables recursion.

```sql
-- Non-recursive
WITH HighEarners AS (
    SELECT * FROM employees WHERE salary > 100000
)
SELECT department, COUNT(*) FROM HighEarners GROUP BY department;

-- Recursive: build an org chart
WITH OrgChart AS (
    SELECT Id, Name, ManagerId, 0 AS Level
    FROM employees WHERE ManagerId IS NULL
    UNION ALL
    SELECT e.Id, e.Name, e.ManagerId, oc.Level + 1
    FROM employees e
    JOIN OrgChart oc ON e.ManagerId = oc.Id
)
SELECT * FROM OrgChart;
```

### 43. What is the difference between UNION and UNION ALL?
- **UNION**: Combines result sets and removes duplicate rows (implicit sort/dedupe, slower)
- **UNION ALL**: Combines result sets keeping duplicates (faster, no dedupe pass)

### 44. What is the difference between EXISTS and IN?
- **EXISTS**: Stops at the first matching row (short-circuits), works well with correlated subqueries and NULLs
- **IN**: Evaluates the full subquery result list; can behave unexpectedly if the list contains NULL

```sql
-- Prefer EXISTS for existence checks on large tables
SELECT d.name FROM departments d
WHERE EXISTS (SELECT 1 FROM employees e WHERE e.dept_id = d.id);
```

### 45. What is a self join?
A table joined with itself, typically to compare rows or model hierarchical data (e.g., employee-manager relationships).

```sql
SELECT e.name AS Employee, m.name AS Manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

### 46. What is the logical order of execution of a SQL query?
`FROM/JOIN` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT/OFFSET`. This is why column aliases from `SELECT` can't be used in `WHERE`, but can be used in `ORDER BY`.

> See [[06-Database#Temporary Objects|Temporary Objects]] below for temp tables, table variables, CTEs, and derived tables compared.

## Keys & Constraints

### 47. What is the difference between a candidate key, primary key, surrogate key, and natural key?
- **Candidate key**: Any column (or set of columns) that could uniquely identify a row
- **Primary key**: The candidate key chosen to be the main identifier
- **Natural key**: A key derived from real-world business data (e.g., email, SSN)
- **Surrogate key**: An artificial key with no business meaning (e.g., auto-increment ID, GUID), preferred when natural keys can change

### 48. What is the difference between a UNIQUE constraint and a PRIMARY KEY?
Both enforce uniqueness, but a table can have only **one** primary key (which also implies NOT NULL) while it can have **multiple** UNIQUE constraints, and UNIQUE columns can allow a single NULL (in most RDBMS).

### 49. What are insertion, update, and deletion anomalies?
Problems caused by poor normalization:
- **Insertion anomaly**: Can't add data without unrelated data also being present (e.g., can't add a course without a student)
- **Update anomaly**: Same fact stored in multiple places, requiring multiple updates and risking inconsistency
- **Deletion anomaly**: Deleting a row unintentionally removes other useful data

Normalization (see [[06-Database#6. What is normalization?|normalization]]) resolves these.

## Indexing Deep Dive

### 50. How does a B-Tree index work?
Most relational databases use a balanced tree (B-Tree/B+Tree) structure where leaf nodes hold sorted key values (and, for clustered indexes, the actual row data). Searches, inserts, and range scans run in O(log n) by traversing from the root down to the matching leaf.

### 51. What is a covering index?
An index that contains all the columns a query needs (in the key or as included columns), so the engine can satisfy the query entirely from the index without a lookup to the base table ("key lookup").

```sql
CREATE INDEX IX_Employees_Dept_Covering
ON employees (department_id) INCLUDE (name, salary);
```

### 52. What is the difference between an index seek and an index scan?
- **Index seek**: Engine navigates directly to matching rows using the index tree — fast, used when the predicate matches the index well (e.g., equality/range on a leading column)
- **Index scan**: Engine reads the entire index (or table) sequentially — slower, happens when the index can't be used selectively or most rows are needed anyway

### 53. When can an index hurt performance?
- Slows down `INSERT`/`UPDATE`/`DELETE` since indexes must also be maintained
- Consumes extra disk space and memory
- Too many indexes can confuse the query optimizer's choice
- Indexes on low-cardinality columns (e.g., a boolean flag) rarely help

## ORM & Entity Framework Core

### 54. What is an ORM and what problems does it solve?
An Object-Relational Mapper (e.g., Entity Framework Core, Dapper) maps database rows to objects, letting developers work with the database using the application's language instead of raw SQL. It reduces boilerplate, provides change tracking, migrations, and LINQ query translation, at some cost to fine-grained control over generated SQL.

### 55. What is the N+1 query problem and how do you avoid it?
Occurs when code loads a list of N parent entities, then issues one additional query per entity to load related data — N+1 total queries instead of 1 or 2.

```csharp
// N+1 problem
var orders = context.Orders.ToList();
foreach (var o in orders)
    Console.WriteLine(o.Customer.Name); // triggers a query per order

// Fixed with eager loading
var orders = context.Orders.Include(o => o.Customer).ToList();
```
Fix with eager loading (`Include`), explicit batching, or projecting only needed columns.

### 56. What is the difference between lazy loading, eager loading, and explicit loading in EF Core?
- **Lazy loading**: Related data is fetched automatically the first time a navigation property is accessed (can cause N+1)
- **Eager loading**: Related data is loaded upfront with the main query via `Include()`
- **Explicit loading**: Related data is loaded on demand via an explicit call (`context.Entry(entity).Collection(...).Load()`)

### 57. What is change tracking in EF Core?
The `DbContext` tracks the original and current state of loaded entities so that calling `SaveChanges()` knows exactly which `INSERT`/`UPDATE`/`DELETE` statements to generate. `AsNoTracking()` disables this for read-only queries to improve performance.

### 58. What is the difference between Code-First and Database-First approaches?
- **Code-First**: Define C# entity classes; EF Core generates the schema and migrations from them
- **Database-First**: An existing database schema is scaffolded (reverse-engineered) into C# entity classes

## Scalability & Data Warehousing

### 59. What is the difference between OLTP and OLAP?
- **OLTP** (Online Transaction Processing): Optimized for many short read/write transactions, normalized schema — e.g., an e-commerce order system
- **OLAP** (Online Analytical Processing): Optimized for complex read-heavy analytical queries over large historical datasets, often denormalized — e.g., a reporting/BI system

### 60. What is the difference between a data warehouse and a data lake?
- **Data warehouse**: Stores structured, processed data optimized for querying and reporting (schema-on-write)
- **Data lake**: Stores raw data in any format (structured, semi-structured, unstructured) at scale, schema is applied when read (schema-on-read)

### 61. What is a star schema vs a snowflake schema?
Both are data-warehouse modeling patterns built around a central fact table:
- **Star schema**: Fact table linked directly to denormalized dimension tables — simpler, faster reads
- **Snowflake schema**: Dimension tables are further normalized into sub-dimensions — less redundancy, more joins

### 62. What is read/write splitting?
A scaling pattern where write operations go to a primary (master) database and read operations are routed to one or more read replicas, reducing load on the primary. Requires tolerating replication lag (eventual consistency) for reads.

### 63. What is the difference between vertical and horizontal scaling for databases?
- **Vertical scaling (scale up)**: Add more CPU/RAM/disk to a single server — simple but has a hardware ceiling
- **Horizontal scaling (scale out)**: Add more servers (replicas or shards, see [[06-Database#17. What is database sharding?|sharding]]) — more complex but scales further

### 64. What is the Saga pattern for distributed transactions?
A way to maintain data consistency across multiple services/databases without a single ACID transaction. A saga is a sequence of local transactions, each with a compensating action to undo it if a later step fails. See [[12-RabbitMQ-MassTransit|RabbitMQ & MassTransit]] for implementing sagas over messaging.

## Temporary Objects

### 65. What is a temporary table?
A table created at runtime that exists only for the duration of a session or scope, then is automatically dropped. Stored in a special system database (e.g., `tempdb` in SQL Server), but otherwise behaves like a real table — it supports indexes, constraints, and statistics.

```sql
CREATE TABLE #TempOrders (
    OrderId INT,
    Total DECIMAL(10,2)
);

INSERT INTO #TempOrders SELECT Id, Total FROM Orders WHERE Status = 'Pending';

SELECT * FROM #TempOrders;
-- Dropped automatically when the session/connection ends, or explicitly:
DROP TABLE #TempOrders;
```

**Local vs global (SQL Server):**
- `#TempTable` (single `#`): **Local** — visible only to the session that created it, dropped when that session disconnects
- `##TempTable` (double `#`): **Global** — visible to all sessions, dropped when the creating session disconnects *and* no other session is referencing it

### 66. What is a table variable and how does it differ from a temp table?
A table variable (`DECLARE @t TABLE (...)`) holds a result set in memory (spilling to `tempdb` if large), scoped to the batch, function, or stored procedure that declares it — it goes out of scope automatically, no explicit `DROP` needed.

| | Temp Table (`#temp`) | Table Variable (`@table`) |
|---|---|---|
| Scope | Session | Batch/procedure |
| Statistics | Yes (query optimizer can estimate rows well) | No/limited (optimizer often assumes 1 row, can misjudge plans) |
| Transaction log | Fully logged | Minimally logged |
| DDL after creation | Allowed (add indexes, constraints) | Not allowed after declaration |
| Indexes | Explicit `CREATE INDEX` | Only via inline `PRIMARY KEY`/`UNIQUE` in declaration |
| Best for | Larger datasets, complex queries needing optimizer stats | Small datasets, simple lookups within a single batch |

### 67. What is the difference between a temp table, a table variable, and a CTE?
- **Temp table**: Physical (session-scoped) table in `tempdb`; best for large intermediate result sets reused across multiple queries
- **Table variable**: In-memory, batch-scoped; best for small, simple result sets
- **CTE** (see [[06-Database#42. What is a CTE (Common Table Expression)?|CTE]]): Not materialized/stored — just a named subquery inlined into the main query each time it's referenced; cannot be indexed and only lives for that one statement, but supports recursion

### 68. What is a derived table?
A subquery used in the `FROM` clause and given an alias, existing only for the duration of that query — similar to a CTE but without a name defined upfront via `WITH`.

```sql
SELECT dept, avg_salary
FROM (
    SELECT department AS dept, AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
) AS DeptAverages
WHERE avg_salary > 60000;
```

## Views & Functions

### 69. What is the difference between a regular view and a materialized view?
- **Regular (standard) view**: Just a stored query — no data is stored; every time it's queried, the underlying SQL re-executes against live tables. Always up to date, but no performance benefit on its own.
- **Materialized view**: The query result is physically stored on disk like a table. Reads are fast (no re-execution), but the data becomes stale until the view is refreshed (manually, on a schedule, or via triggers depending on the engine). Common in PostgreSQL (`CREATE MATERIALIZED VIEW`), Oracle, and analytics/OLAP workloads; SQL Server's closest equivalent is an **indexed view**.

```sql
-- PostgreSQL / Oracle style
CREATE MATERIALIZED VIEW dept_avg_salary AS
SELECT department, AVG(salary) AS avg_salary
FROM employees
GROUP BY department;

REFRESH MATERIALIZED VIEW dept_avg_salary; -- data updated on demand
```

| | Regular View | Materialized View |
|---|---|---|
| Storage | None (just SQL) | Stores actual result data |
| Read speed | Same as underlying query | Fast (pre-computed) |
| Data freshness | Always current | Stale until refreshed |
| Write overhead | None | Refresh cost |
| Best for | Simplifying/restricting access to live data | Expensive aggregations queried often, where some staleness is acceptable |

See [[06-Database#26. What is a view?|regular views]] above for the base concept.

### 70. What is a scalar function?
A user-defined function that takes parameters and returns a **single value** (e.g., an int, string, date). Used like a built-in function, typically in `SELECT`, `WHERE`, or computed columns.

```sql
CREATE FUNCTION dbo.GetFullName (@FirstName NVARCHAR(50), @LastName NVARCHAR(50))
RETURNS NVARCHAR(101)
AS
BEGIN
    RETURN @FirstName + ' ' + @LastName;
END;

SELECT dbo.GetFullName(FirstName, LastName) AS FullName FROM Employees;
```
**Caution:** Scalar UDFs called per-row in a query can be a major performance problem (they often prevent parallelism/inlining in older SQL Server versions) — prefer inline table-valued functions or computed columns where possible.

### 71. What is a table-valued function (TVF)?
A user-defined function that returns a **table** (a full result set) instead of a single value, so it can be queried and joined like a regular table.

- **Inline TVF**: Body is a single `RETURN (SELECT ...)` statement — gets expanded/optimized like a view, generally fast.
- **Multi-statement TVF**: Declares a `TABLE` return variable, populated with multiple statements inside `BEGIN...END` — more flexible (loops, multiple inserts) but generally slower since the optimizer treats it more like a black box.

```sql
-- Inline TVF
CREATE FUNCTION dbo.GetEmployeesByDept (@DeptId INT)
RETURNS TABLE
AS
RETURN (SELECT Id, Name, Salary FROM Employees WHERE DepartmentId = @DeptId);

SELECT * FROM dbo.GetEmployeesByDept(3);
```

### 72. What is the difference between a scalar function and a table-valued function?
| | Scalar Function | Table-Valued Function |
|---|---|---|
| Returns | Single value | A table (result set) |
| Usable in `FROM`/`JOIN` | No | Yes |
| Typical use | Computed value, formatting, lookups | Reusable parameterized query, replacing a view that needs arguments |
| Performance risk | High if called per-row on large sets | Inline TVFs perform well; multi-statement TVFs can be slow |

### 73. What is the difference between a CTE and a subquery?
- **Subquery**: A query nested inside another (in `SELECT`, `FROM`, `WHERE`); defined inline where it's used, can't reference itself, harder to read when nested deeply
- **CTE** (see [[06-Database#42. What is a CTE (Common Table Expression)?|CTE]]): Named upfront with `WITH`, can be referenced multiple times in the same statement, supports recursion, and generally improves readability for multi-step logic — but in most engines it's just syntactic sugar; the optimizer often produces the same execution plan as an equivalent subquery (it is **not** automatically materialized/cached, unlike a temp table).

```sql
-- Subquery
SELECT name FROM employees
WHERE dept_id IN (SELECT id FROM departments WHERE budget > 1000000);

-- Equivalent CTE
WITH BigDepts AS (
    SELECT id FROM departments WHERE budget > 1000000
)
SELECT name FROM employees WHERE dept_id IN (SELECT id FROM BigDepts);
```
