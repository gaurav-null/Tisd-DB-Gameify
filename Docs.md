# College Match Organizing Platform API Documentation

## Base URL
`https://yourdomain.com/api`

## Authentication
All endpoints (except `/register` and `/login`) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## User Management

### Register a new user
`POST /register`

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "role": "student",
  "college_id": "uuid-of-college"
}
```

**Response:**
- Success: 201 Created
- Error: 400 Bad Request (if validation fails or email exists)

### Login
`POST /login`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "jwt.token.here"
}
```

### Get user profile
`GET /users/<user_id>`

**Response:**
```json
{
  "id": "user-uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "student",
  "college_id": "college-uuid",
  "skill_level": 3
}
```

## College Management (Admin only)

### Create college
`POST /colleges`

**Request Body:**
```json
{
  "name": "Tech University",
  "location": "New York",
  "contact_email": "admin@techuniv.edu"
}
```

### Add restricted days
`POST /colleges/<college_id>/restricted-days`

**Request Body:**
```json
{
  "day_of_week": 1, // Monday (0=Sunday, 6=Saturday)
  "is_restricted": true,
  "restricted_start_time": "08:00:00",
  "restricted_end_time": "17:00:00"
}
```

## Event Management

### Create event
`POST /events`

**Request Body:**
```json
{
  "name": "Annual Sports Day",
  "description": "Yearly sports competition",
  "start_date": "2023-11-15T09:00:00",
  "end_date": "2023-11-15T17:00:00",
  "max_participants": 100,
  "registration_deadline": "2023-11-10T23:59:59"
}
```

**Response:**
- Success: 201 Created with event details
- Error: 400 if scheduling during restricted hours

## Match Management

### Create match
`POST /matches`

**Request Body:**
```json
{
  "game_category_id": "basketball-uuid",
  "scheduled_time": "2023-11-16T14:00:00",
  "min_players": 4,
  "max_players": 10,
  "skill_level_range": 2
}
```

### Register for match
`POST /matches/<match_id>/register`

**Response:**
- Success: 201 Created with participation details
- Error: 400 if match is full or skill level mismatch

## Team Management

### Create team
`POST /teams`

**Request Body:**
```json
{
  "name": "The Champions",
  "skill_level": 5
}
```

### Join team
`POST /teams/<team_id>/join`

## Venue & Equipment (Admin only)

### Add venue
`POST /venues`

**Request Body:**
```json
{
  "name": "Main Gymnasium",
  "location": "Building A",
  "capacity": 200
}
```

### Add equipment
`POST /equipment`

**Request Body:**
```json
{
  "name": "Basketball",
  "quantity": 10,
  "condition": "good"
}
```

## Scheduling

### Create schedule
`POST /schedules`

**Request Body:**
```json
{
  "match_id": "match-uuid",
  "venue_id": "venue-uuid",
  "start_time": "2023-11-16T14:00:00",
  "end_time": "2023-11-16T16:00:00",
  "equipment_needed": "5 basketballs, 10 jerseys"
}
```

**Response:**
- Success: 201 Created
- Error: 400 if venue conflict or unavailable

## Error Responses

All error responses follow this format:
```json
{
  "message": "Error description",
  "code": 400
}
```

Common error codes:
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid/missing token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 500: Internal Server Error

## Rate Limits
- 100 requests per minute per IP address
- 1000 requests per day per user

---

This documentation provides an overview of the API endpoints. For detailed request/response examples and additional endpoints, refer to the full API specification.
