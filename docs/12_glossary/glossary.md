# arc42 — Section 12: Glossary

Terms used throughout the BookRover project documentation and codebase.

---

| Term | Definition |
|------|-----------|
| **Admin** | A dedicated user role responsible for managing group leaders and bookstore records. Has a separate login; not visible to sellers. |
| **ADR** | Architecture Decision Record — a document capturing a significant design or technology decision, its context, the options considered, and the rationale for the choice made. |
| **arc42** | A pragmatic software architecture documentation template with 12 sections. Used in BookRover to document the system architecture. |
| **AWS** | Amazon Web Services — the cloud platform used to host BookRover. |
| **API Gateway** | AWS service that exposes the FastAPI backend as HTTP endpoints. BookRover uses the HTTP API type (simpler and cheaper than REST API). |
| **Bookstore** | The local bookstore that provides books to the group on consignment. Represented as a data entity in BookRover; the bookstore owner is not a direct app user. |
| **BookRover** | The name of this door-to-door book selling management application. |
| **boto3** | The official AWS Python SDK. Used by the FastAPI backend to interact with DynamoDB. |
| **CDN** | Content Delivery Network. CloudFront is the CDN used to serve the React frontend from edge locations closest to the user. |
| **CloudFront** | AWS CDN service. Serves the React frontend from S3 and routes API calls to API Gateway. Enforces HTTPS. |
| **Cold Start** | The latency penalty when Lambda initializes a new execution environment for the first time (or after inactivity). Typically < 1 second for Python + FastAPI. |
| **Consignment** | A business arrangement where the bookstore provides books to the group without upfront payment. Payment is made after books are sold; unsold books are returned. |
| **current_count** | The number of copies of a book currently in a seller's hand (not yet sold or returned). Decremented atomically on each sale. |
| **DynamoDB** | AWS serverless NoSQL database. Used as the sole data store for BookRover. On-demand billing. |
| **DynamoDB Local** | An official AWS-provided Docker image that emulates DynamoDB locally. Used for local development (requires Docker Desktop). |
| **FastAPI** | A modern Python web framework for building APIs. Provides automatic OpenAPI documentation and Pydantic-based request validation. |
| **GSI** | Global Secondary Index — a DynamoDB index that enables querying on non-primary-key attributes. BookRover uses GSIs to query sellers by group leader, inventory by seller, and sales by seller. |
| **Group Leader** | A user role that oversees a team of sellers and is associated with one or more bookstores. Views the seller performance dashboard. |
| **IAM** | Identity and Access Management — AWS service for controlling who can do what with AWS resources. Lambda execution role uses IAM to restrict access to BookRover's DynamoDB tables only. |
| **initial_count** | The total number of copies of a book collected from the bookstore at the start. Never changes after creation. |
| **IaC** | Infrastructure as Code — defining AWS infrastructure in code (Terraform) rather than manually through the Console. Planned for Phase 7. |
| **Lambda** | AWS serverless compute service. BookRover's FastAPI backend runs as a Lambda function, triggered by API Gateway. |
| **Mangum** | A Python library that adapts ASGI applications (like FastAPI) to the AWS Lambda + API Gateway event format. |
| **moto** | A Python library that mocks AWS services (including DynamoDB) in-memory for unit and integration testing. No real AWS calls are made. |
| **moto_server** | `moto`'s standalone HTTP server mode that emulates DynamoDB's API locally. Used as a DynamoDB substitute during development when Docker is not available. |
| **OAC** | Origin Access Control — the AWS-recommended way for CloudFront to access a private S3 bucket securely. |
| **Pydantic** | Python library for data validation using type annotations. Used by FastAPI for request and response models. |
| **Return** | The act of a seller physically returning unsold books and collected money to the bookstore at the end of a selling round. |
| **Return Summary** | The page showing a seller how many unsold books they have, their cost value, and the total money collected from sales — all to be returned to the bookstore. |
| **S3** | AWS Simple Storage Service. Hosts the compiled React frontend as static files. |
| **SAA-C03** | AWS Solutions Architect Associate exam (version C03). Building BookRover on AWS serves as a practical study aid for this certification. |
| **Seller** | A user who collects books from the bookstore (via their group leader), sells them door-to-door, and returns unsold books + money. Each seller manages their own independent inventory. |
| **SaleItem** | A single line in a sale — one book title + quantity sold + price. Stored as a nested list within the Sale document. Values are snapshotted at the time of sale. |
| **Snapshot** | In SaleItem and ReturnItem, key values (book name, language, price) are copied at the time of the transaction so that historical records remain accurate even if book details change later. |
| **SOLID** | Five object-oriented design principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Applied throughout the BookRover codebase. |
| **spec-kit** | A collection of markdown specification files (data models, API spec, page spec, architecture) that give GitHub Copilot the context it needs to generate accurate, project-aware code. |
| **Terraform** | An Infrastructure as Code tool used to define and provision cloud infrastructure. Planned for Phase 7 to codify the manual AWS Console setup. |
| **UUID v4** | Universally Unique Identifier (version 4, random). Used as the primary key for all BookRover entities. |
| **uvicorn** | An ASGI server for Python. Used to run FastAPI locally during development. |
| **Well-Architected Framework** | AWS's guidelines for building secure, high-performing, resilient, and efficient cloud infrastructure across five pillars: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization. |
