🛡️ SilentShield

Data-Driven Banking Duress Detection & Behavioural Security Platform

SilentShield is a cybersecurity and data engineering project designed to explore how banking systems could detect potential duress, fraudulent activity, and unusual user behaviour while maintaining a discreet user experience.

The project combines software engineering, data engineering, cybersecurity, behavioural analytics, and psychology into a single platform.

⚠️ Educational/Research Project: SilentShield is a prototype and does not connect to real banking systems or process real customer financial information.

🎯 Project Objective

Traditional banking security systems primarily focus on whether a user has entered the correct credentials.

SilentShield explores a broader question:

Can behavioural and transactional data be used to identify potentially dangerous or abnormal banking activity and trigger additional security controls?

The platform simulates banking events such as:

ATM withdrawals

Authentication attempts

Transaction activity

Device changes

Location changes

Unusual transaction patterns

Potential duress events

The collected data is processed through a data pipeline and analysed by a security engine.

🧠 Psychology + Cybersecurity

A key aspect of SilentShield is the application of human behaviour and psychology to cybersecurity.

Users do not always behave consistently when they are under stress, experiencing social engineering, or responding to an unusual situation.

The system therefore explores behavioural patterns such as:

Normal transaction behaviour

Authentication behaviour

Transaction frequency

Time-of-day behaviour

Device usage

Location patterns

Behavioural deviations

Responses to security events

The purpose is not to label a person as malicious.

Instead, the system focuses on identifying behavioural deviations that may require additional verification or security investigation.

🏗️ System Architecture

                         BANKING EVENTS
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
           ATM Events     Transactions     Login Events
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                       DATA INGESTION
                              │
                            Kafka
                              │
                              ▼
                      DATA PROCESSING
                       Python / Spark
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Data Validation            Security Rules
                 │                         │
                 └────────────┬────────────┘
                              ▼
                         DATA STORAGE
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         PostgreSQL       Data Lake      Data Warehouse
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                     BEHAVIOURAL ANALYTICS
                              │
                              ▼
                       RISK ENGINE
                              │
                              ▼
                         REST API
                              │
                              ▼
                      SECURITY DASHBOARD


🔐 Core Security Concept

SilentShield explores the concept of covert duress authentication.

A future implementation may allow a customer to authenticate normally while providing an alternative authentication signal that indicates potential duress.

For example:

Normal authentication
        ↓
Normal transaction flow

Potential duress signal
        ↓
Apparently normal transaction
        ↓
Silent security event
        ↓
Risk analysis
        ↓
Security monitoring


The system is designed so that a potential attacker would not necessarily be informed that a security event has been generated.

The prototype will focus on exploring the technical feasibility and security implications of this concept rather than implementing it in a real banking environment.

💳 Duress Balance & Silent Account State

SilentShield will also explore a silent duress balance state for the prototype.

The key design principle is that the user should not have to press an "EXIT DURESS MODE" button or perform any action that could reveal to another person that duress protection has been activated.

Instead, the authentication flow can use two PINs:

Duress PIN — opens a restricted shadow balance that can be used during a coercive situation.

Real PIN — returns the customer to the normal account state and reveals the actual balance.

The person coercing the customer would see what appears to be a normal banking session. The existence of the second account state would not need to be exposed through the normal interface.

Example flow

Duress PIN
    ↓
Shadow / Duress Mode
    ↓
Visible balance: R600
    ↓
User logs out
    ↓
Next day
    ↓
Duress PIN
    ↓
Visible balance: R600
    ↓
Withdraw R200
    ↓
Visible balance: R400
    ↓
Real PIN
    ↓
Normal Mode
    ↓
Actual account balance

The duress balance persists between sessions. Logging out does not automatically reveal or disable the state.

🎬 Demonstration Scenario

For a project demonstration, SilentShield can simulate:

REAL ACCOUNT BALANCE
R20,000
        ↓
Enter Duress PIN
        ↓
DUress / SHADOW MODE
Visible balance: R1,000
        ↓
Withdraw R400
        ↓
Visible balance: R600
        ↓
Log out
        ↓
Come back the next day
        ↓
Enter Duress PIN
        ↓
Visible balance: R600
        ↓
Withdraw R200
        ↓
Visible balance: R400
        ↓
Enter Real PIN
        ↓
NORMAL MODE
        ↓
Actual balance: R19,400

This demonstrates that the duress state is persistent across sessions while keeping the normal authentication experience unchanged.

Security model

The prototype should keep the two balances logically separate:

CUSTOMER ACCOUNT
        │
        ├── REAL BALANCE
        │      R20,000
        │
        └── DURESS BALANCE
               R1,000
                  │
                  ├── Withdraw R400
                  │       ↓
                  │     R600
                  │
                  └── Withdraw R200
                          ↓
                        R400

The prototype should record duress transactions as security events so that the security engine can analyse them without exposing the duress state to the person interacting with the account.

⚠️ Prototype safety note: This is a simulated banking feature for educational research. It should not be connected to real customer accounts or used as a real-world banking security mechanism without extensive security, legal, privacy, fraud, recovery, and financial-system review.

📊 Data Engineering Pipeline

Data engineering is a major component of SilentShield.

The platform generates and processes simulated banking events.

Data ingestion

Events are generated from simulated:

ATMs

banking applications

authentication systems

transaction systems

devices

These events can be streamed using Apache Kafka.

Data processing

The pipeline performs:

validation

cleaning

transformation

deduplication

enrichment

feature generation

Example behavioural features:

customer_id
transactions_last_24h
average_transaction_amount
failed_authentication_attempts
new_device
new_location
night_transactions
transaction_velocity
behaviour_deviation_score


Data storage

Different storage layers can be used for different purposes:

PostgreSQL

Transactional and application data.

Data Lake

Raw historical events.

Data Warehouse

Processed data for analytics and reporting.

🚨 Security Detection

The security engine analyses events and identifies potentially suspicious activity.

Example:

Customer: 1042

Normal behaviour
-----------------------------
Average withdrawal: R850
Typical time: 08:00 - 18:00
Typical location: Gauteng
Average transactions/day: 4


Current activity
-----------------------------
Withdrawal: R5,000
Time: 02:13
Location: Unknown ATM
Transactions: 12


Behavioural deviation: HIGH

Security risk: HIGH


The system can generate security events based on combinations of signals rather than relying on a single event.

🧠 Behavioural Analytics

SilentShield establishes a baseline of simulated user behaviour.

For example:

                 NORMAL BEHAVIOUR
                        │
                        ▼
                Behavioural Baseline
                        │
                        ▼
                  New Activity
                        │
                        ▼
              Compare Against Baseline
                        │
                        ▼
               Behavioural Deviation
                        │
                        ▼
                  Risk Analysis


This provides an opportunity to explore:

anomaly detection

behavioural analytics

machine learning

human factors in cybersecurity

fraud detection

🛠️ Technology Stack

Backend

Java

Spring Boot

REST APIs

PostgreSQL

JUnit

Data Engineering

Python

SQL

Apache Kafka

Apache Spark

Apache Airflow

Data Warehousing

ETL / ELT

Cybersecurity

Authentication

Authorization

RBAC

JWT/OAuth

Secure API design

Audit logging

Threat detection

Anomaly detection

Frontend

React

TypeScript

HTML

CSS

Infrastructure

Docker

GitHub Actions

AWS

Terraform

Kubernetes

Technologies will be introduced progressively as the project develops.

📁 Planned Project Structure

silentshield/
│
├── backend/
│   ├── src/
│   └── pom.xml
│
├── data-pipeline/
│   ├── ingestion/
│   ├── processing/
│   ├── transformations/
│   └── tests/
│
├── security-engine/
│   ├── detection/
│   ├── risk/
│   └── rules/
│
├── frontend/
│   ├── src/
│   └── components/
│
├── infrastructure/
│   ├── docker/
│   ├── terraform/
│   └── kubernetes/
│
├── docs/
│   ├── architecture/
│   ├── database/
│   ├── security/
│   └── research/
│
├── tests/
│
└── README.md


🗃️ Example Data Model

CUSTOMER
   │
   ├──── ACCOUNT
   │
   └──── DEVICE
          │
          ▼
     TRANSACTION
          │
          ▼
   AUTHENTICATION_EVENT
          │
          ▼
     SECURITY_EVENT
          │
          ▼
       RISK_SCORE


Potential entities include:

Customer

Account

Transaction

ATM

Device

Authentication Event

Security Event

Risk Assessment

Behaviour Profile

Duress Credential

Duress Balance

Audit Event

🔬 Research Questions

SilentShield can also be used to explore several research questions:

1. Human behaviour

How does abnormal banking behaviour differ from a user's established behavioural baseline?

2. Cybersecurity

Can multiple low-risk events collectively indicate a potentially high-risk security situation?

3. Data engineering

How can high-volume banking events be processed in near real time?

4. Fraud detection

Can behavioural features improve the detection of potentially fraudulent transactions?

5. Human factors

How can security mechanisms be designed without increasing cognitive burden for users?

📈 Development Roadmap

Phase 1 — Software Engineering

Create Spring Boot backend

Design REST API

Create PostgreSQL database

Implement transaction management

Add unit and integration tests

Phase 2 — Authentication

User authentication

Password security

JWT

Role-based access control

Audit logging

Duress PIN authentication

Separate real and duress account states

Persistent duress balance across sessions

Silent return to normal mode through the real PIN

Phase 3 — Data Engineering

Create simulated banking data

Build ingestion service

Introduce Kafka

Build ETL pipeline

Implement data validation

Create data warehouse

Add Airflow orchestration

Phase 4 — Cybersecurity

Security event detection

Authentication anomaly detection

Transaction anomaly detection

Duress-mode transaction monitoring

Risk scoring

Security alerts

Incident dashboard

Phase 5 — Behavioural Analytics

Establish behavioural baselines

Generate behavioural features

Detect behavioural deviations

Analyse human factors

Experiment with machine learning

Phase 6 — Cloud

Dockerise services

Create CI/CD pipeline

Deploy to AWS

Implement monitoring

Infrastructure as Code

Explore Kubernetes

🧪 Testing

The project will include multiple levels of testing:

Unit Testing

Individual services and functions.

Integration Testing

Communication between:

API → Database
API → Kafka
Kafka → Processing
Processing → Database


Security Testing

Testing for:

authentication weaknesses

authorization issues

insecure APIs

injection attacks

rate limiting

credential security

Data Quality Testing

Testing for:

missing values

duplicates

invalid transactions

schema violations

incorrect timestamps

🔒 Privacy & Ethical Considerations

SilentShield is designed as an educational and research prototype.

No real banking credentials, PINs, account numbers, or customer financial information should be used.

The project should follow privacy-by-design principles, including:

data minimisation

anonymisation

access control

encryption

auditability

secure storage

Behavioural analytics should be treated as risk signals rather than definitive evidence of wrongdoing.

🌍 Potential Industry Applications

Although SilentShield is designed around banking, the underlying architecture can be adapted to other industries.

Banking & FinTech

Fraud detection

Account takeover detection

Transaction monitoring

Authentication security

Telecommunications

Network anomaly detection

SIM/account takeover detection

Customer behaviour analytics

Security event monitoring

Large-scale event processing

Technology Companies

Application security

Identity management

Security monitoring

Behaviour analytics

Enterprise

Insider threat detection

Security operations

Access monitoring

Data security

👨‍💻 Developer Goals

This project is being developed as part of my transition into technology, with a focus on building practical skills across:

Software Engineering

Data Engineering

Cybersecurity

Cloud Computing

Behavioural Analytics

Human Factors

The long-term goal is to develop systems that combine secure software, large-scale data processing, and an understanding of human behaviour.

⭐ Future Vision

SilentShield will evolve from a simple banking-security prototype into a distributed security analytics platform capable of processing large volumes of simulated events in near real time.

The long-term architecture will explore:

Software Engineering
        +
Data Engineering
        +
Cybersecurity
        +
Cloud Computing
        +
Psychology
        ↓
Human-Centred Security Systems


📜 Disclaimer

SilentShield is an educational and research project.

It is not connected to any bank, does not process real financial transactions, and should not be used to handle real customer banking credentials or financial information.

📄 License

This project is intended for educational and research purposes.