# Network Feature API Documentation

## Overview
The Network Feature API allows users to follow each other and view real-time regret management progress, creating accountability networks around daily habit tracking.

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
```
https://your-domain.com/api/network/
```

## Endpoints

### 1. Validate Username for Network Addition

**Endpoint:** `GET /api/network/validate/<username>/`

**Description:** Check if a username is valid for following before creating the relationship.

**Parameters:**
- `username` (path): The username to validate

**Response:**
```json
{
    "username": "johndoe",
    "user_id": 123,
    "allow_networking": true
}
```

**Error Responses:**
- `400 Bad Request`: Username is required
- `403 Forbidden`: This user has networking disabled
- `404 Not Found`: User not found
- `409 Conflict`: You are already following this user / You cannot follow yourself
- `500 Internal Server Error`: Network operation failed

**Example:**
```bash
curl -X GET "https://your-domain.com/api/network/validate/johndoe/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

### 2. Follow User

**Endpoint:** `POST /api/network/follow/<username>/`

**Description:** Create a follow relationship with another user.

**Parameters:**
- `username` (path): The username to follow

**Response:**
```json
{
    "message": "Successfully followed johndoe",
    "network_id": 456,
    "following": "johndoe"
}
```

**Error Responses:**
- `400 Bad Request`: Username is required
- `403 Forbidden`: This user has networking disabled
- `404 Not Found`: User not found
- `409 Conflict`: You are already following this user / You cannot follow yourself
- `500 Internal Server Error`: Network operation failed

**Example:**
```bash
curl -X POST "https://your-domain.com/api/network/follow/johndoe/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

### 3. Unfollow User

**Endpoint:** `DELETE /api/network/unfollow/<username>/`

**Description:** Remove a follow relationship with another user.

**Parameters:**
- `username` (path): The username to unfollow

**Response:**
```json
{
    "message": "Successfully unfollowed johndoe"
}
```

**Error Responses:**
- `400 Bad Request`: Username is required
- `404 Not Found`: User not found / You are not following this user
- `500 Internal Server Error`: Network operation failed

**Example:**
```bash
curl -X DELETE "https://your-domain.com/api/network/unfollow/johndoe/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

### 4. Get Network Lists

**Endpoint:** `GET /api/network/list/<list_type>/`

**Description:** Get a list of users you're following or users following you, including their latest checklist scores and creation timestamps.

**Parameters:**
- `list_type` (path): Either "following" or "followers"

**Response:**
```json
{
    "list_type": "following",
    "count": 2,
    "users": [
        {
            "id": 123,
            "username": "johndoe",
            "regret_index": 0.75,
            "checklist_created_at": "2025-08-17T08:00:00Z",
            "allow_networking": true,
            "followers_count": 5,
            "following_count": 3,
            "date_joined": "2025-01-15T10:30:00Z"
        },
        {
            "id": 456,
            "username": "janedoe",
            "regret_index": 0.25,
            "checklist_created_at": "2025-08-16T14:20:00Z",
            "allow_networking": false,
            "followers_count": 8,
            "following_count": 2,
            "date_joined": "2025-02-01T14:20:00Z"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid list type. Use 'following' or 'followers'
- `500 Internal Server Error`: Network operation failed

**Examples:**
```bash
# Get users you're following
curl -X GET "https://your-domain.com/api/network/list/following/" \
  -H "Authorization: Bearer <your_jwt_token>"

# Get users following you
curl -X GET "https://your-domain.com/api/network/list/followers/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

### 5. Update Network Settings

**Endpoint:** `PATCH /api/network/settings/`

**Description:** Update your networking preferences (allow/disallow others from following you).

**Request Body:**
```json
{
    "allow_networking": false
}
```

**Response:**
```json
{
    "message": "Networking settings updated successfully",
    "allow_networking": false
}
```

**Error Responses:**
- `400 Bad Request`: allow_networking field is required
- `500 Internal Server Error`: Failed to update networking settings

**Example:**
```bash
curl -X PATCH "https://your-domain.com/api/network/settings/" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"allow_networking": false}'
```

---

### 6. Get Current Network Settings

**Endpoint:** `GET /api/network/settings/`

**Description:** Retrieve your current networking preferences.

**Response:**
```json
{
    "allow_networking": true,
    "message": "Networking settings retrieved successfully"
}
```

**Error Responses:**
- `500 Internal Server Error`: Failed to retrieve networking settings

**Example:**
```bash
curl -X GET "https://your-domain.com/api/network/settings/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

## Data Models

### User Model (Updated)
```json
{
    "id": 123,
    "username": "johndoe",
    "is_active": true,
    "allow_networking": true,
    "followers_count": 5,
    "following_count": 3,
    "date_joined": "2024-01-15T10:30:00Z"
}
```

### Network Model
```json
{
    "id": 456,
    "follower": 123,
    "follower_username": "johndoe",
    "following": 789,
    "following_username": "janedoe",
    "created_at": "2024-03-15T09:00:00Z"
}
```

### Network User (for lists)
```json
{
    "id": 123,
    "username": "johndoe",
    "regret_index": 0.75,
    "checklist_created_at": "2025-08-17T08:00:00Z",
    "allow_networking": true,
    "followers_count": 5,
    "following_count": 3,
    "date_joined": "2025-01-15T10:30:00Z"
}
```

**Key Changes:**
- `regret_index`: Now returns actual score from latest checklist (not calculated)
- `checklist_created_at`: Latest checklist creation time (not filtered by today)
- `allow_networking`: Shows if user allows others to follow them
- Users without checklists are excluded from the response
- Frontend handles all date filtering and logic

---

## Regret Index

The **regret_index** is the actual score from the user's latest checklist:

- **Source**: Latest checklist score (regardless of date)
- **Range**: 0.0 to 1.0
- **0.0**: Perfect day - all regrets resolved successfully
- **0.5**: Half of regrets resolved
- **1.0**: No regrets resolved

**Note**: The backend no longer calculates regret indexes or filters by today's date. It simply returns the score from the most recent checklist, allowing the frontend to handle all date logic and filtering.

## Checklist Creation Time

The **checklist_created_at** field shows when the user created their latest checklist:

- **Format**: ISO 8601 with UTC timezone
- **Example**: `"2025-08-17T18:00:00Z"`
- **Breakdown**: `YYYY-MM-DDTHH:mm:ssZ`
  - Date: YYYY-MM-DD (2025-08-17)
  - Time: HH:mm:ss (18:00:00)
  - Timezone: Z (Zulu time = UTC)
  - Separator: T between date and time
- **Source**: Latest checklist creation time (regardless of date)
- **Timezone**: Always in UTC (Z suffix)
- **Never null**: Users without checklists are excluded from the response

This field is useful for:
- Showing when users last created a checklist
- Understanding user activity patterns
- Providing context for the regret index
- Perfect compatibility with JavaScript `new Date()` parsing

## Networking Status

The **allow_networking** field indicates whether a user allows others to follow them:

- **`true`**: User allows networking (others can follow)
- **`false`**: User has disabled networking (others cannot follow)
- **Default**: `true` (networking enabled by default)

This field is useful for:
- Showing networking status in user profiles
- Displaying appropriate follow/unfollow buttons
- Indicating when users have disabled networking
- Handling networking permissions in the frontend

---

## Error Handling

### Standard Error Response Format
```json
{
    "error": "Error message description"
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created (follow relationship)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid/missing JWT)
- **403**: Forbidden (networking disabled)
- **404**: Not Found (user not found)
- **409**: Conflict (already following, self-following)
- **500**: Internal Server Error

---

## Rate Limiting

To prevent abuse, the following endpoints have rate limiting:
- Follow/Unfollow operations: 10 requests per minute per user
- Network list requests: 60 requests per minute per user

---

## Best Practices

### For Frontend Developers
1. **Always validate usernames** before showing follow buttons
2. **Cache network lists** to reduce API calls
3. **Handle 403 errors** gracefully when users have networking disabled
4. **Show loading states** during follow/unfollow operations
5. **Update local state** immediately for better UX

### For API Consumers
1. **Handle all error responses** appropriately
2. **Use the validation endpoint** before attempting to follow
3. **Implement proper error handling** for network failures
4. **Respect rate limits** to avoid being blocked
5. **Cache responses** when appropriate

---

## Integration Examples

### Complete Follow Flow
```javascript
// 1. Validate username
const validation = await fetch('/api/network/validate/johndoe/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

if (validation.ok) {
    // 2. Follow user
    const follow = await fetch('/api/network/follow/johndoe/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (follow.ok) {
        // 3. Update UI
        updateFollowButton(true);
        updateFollowerCount();
    }
}
```

### Get and Update Networking Settings
```javascript
// 1. Get current networking status
const getSettings = await fetch('/api/network/settings/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

if (getSettings.ok) {
    const currentSettings = await getSettings.json();
    console.log('Current networking:', currentSettings.allow_networking);
    
    // 2. Update networking settings
    const updateSettings = await fetch('/api/network/settings/', {
        method: 'PATCH',
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            allow_networking: !currentSettings.allow_networking
        })
    });
    
    if (updateSettings.ok) {
        const newSettings = await updateSettings.json();
        console.log('Updated networking:', newSettings.allow_networking);
    }
}
```

### Display Network with Regret Indexes
```javascript
// Get following list with regret indexes
const response = await fetch('/api/network/list/following/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

if (response.ok) {
    const data = await response.json();
    
    // Display users with their regret indexes and checklist creation times
    data.users.forEach(user => {
        const checklistTime = user.checklist_created_at 
            ? new Date(user.checklist_created_at).toLocaleTimeString()
            : 'No checklist today';
            
        displayUser(user.username, user.regret_index, checklistTime);
    });
}
```

---

## Support

For technical support or questions about the Network Feature API, please refer to the main application documentation or contact the development team. 