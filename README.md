# CP Problem Tracker API

A REST API for tracking competitive programming problems — log problems you've solved, filter and search them, and view your solve stats by rating. Built with Flask, as a hands-on project to learn backend development from first principles.

## Features

- User signup/login with JWT authentication
- Full CRUD on tracked problems (add, view, update, mark solved, delete)
- Filter problems by tag, solved status, and rating range
- Per-rating solve stats (total vs. solved, computed with database aggregation)
- Ownership checks — users can only view or modify their own problems
- Logout via token blocklisting

## Tech Stack

- **Flask** — web framework
- **Flask-SQLAlchemy** — ORM / database layer
- **Flask-JWT-Extended** — authentication
- **Werkzeug** — password hashing
- **SQLite** — database

## Setup

1. Clone the repo:
```bash
   git clone https://github.com/PranshuNalwa/CP-Problem-Tracker.git
   cd CP-Problem-Tracker
```
 
2. Install dependencies:
```bash
   pip install -r requirements.txt
```
 
3. Create a `.env` file in the project root with:
```
   SECRET_KEY=your-secret-key-here
```
 
4. Run the app:
```bash
   python run.py
```
 
   The API will be available at `http://127.0.0.1:5000`.

## Authentication
 
`/signin` and `/login` both return a JWT access token. Include it on every other request as a header:
 
```
Authorization: Bearer <your-token>
```

## API Endpoints
| Method    | Endpoint                 | Description                                                                                |
|-----------|--------------------------|--------------------------------------------------------------------------------------------|
| POST      | `/signin`                | Signing in the user,returns a JWT Token                                                    |   
| POST      | `/login`                 | logging in the user,returns a JWT Token                                                    |
| POST      | `/logout`                | logging out the user (revokes the current token)                                           |
| POST      | `/users/<id>/problems`   | For adding a new Problem to a user                                                         |
| PUT       | `/problems/<id>`         | To update a Problem of a user                                                              |
| DELETE    | `/problems/<id>`         | To delete a Problem of a user                                                              |
| PATCH     | `/problems/<id>`         | To markdown a problem as solved                                                            |
| GET       | `/problems/<id>`         | To view a single problem                                                                   |
| GET       | `/users/<id>/problems`   | View all problems for a user; supports optional filters tag, status, minrating, maxrating  |
| GET       | `/users/<id>/stats`      | Shows the number of problem total and solved group by rating                               |


## What I Learned / Design Notes

Building this project taught me how to design RESTAPI from scratch. Starting from raw HTTP concepts and learning to work through endpoints conventions (GET vs PUT 
vs PATCH idempotency).

I also learnt about JWT - starting from a hardcoded token to understand the mechanics - to making a auth-checking mechanism from scratch, after this I switched to JWT when I needed to know the users identity to fix ownership checks. 

I also used Token Blocklisting for logout, and why we need to store jti in the database nudged me to understand the mechanics behind what a token contains and how its designed. 

On the database side I learned about SQLAlchemy beyond the basic inserts, I combined different filters onto a single query using filter_by() and where(), also I built a stats endpoint using group_by() and conditional aggregation to compute solved/total counts for every rating.

I also restructured my whole app into blueprints and an application factory once a single file was becoming hard to navigate.
