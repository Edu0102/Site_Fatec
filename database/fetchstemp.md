# Temporary fetch() tests

Paste these commands into the browser console while the ASP.NET server is running.
The commands use the same cookie session established by `/login`. After a successful login,
an admin account can access admin-only endpoints and a basic account can access normal endpoints.

Use values that match the data in `database.db`. Replace IDs such as `1`, `2`, and `999`
with IDs returned by the endpoints.

## Existing base endpoint

```javascript
// Success: server is running
fetch("/")
  .then(async r => console.log("GET /", r.status, await r.text()))
```

## Register and login

```javascript
// Success: register a new basic user
fetch("/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Ana Silva",
    email: "ana@test.com",
    password: "mypassword123"
  })
}).then(async r => console.log("POST /register success", r.status, await r.text()))
```

```javascript
// Validation error: missing required fields
fetch("/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "", email: "", password: "" })
}).then(async r => console.log("POST /register validation", r.status, await r.text()))
```

```javascript
// Conflict: register the same email twice
fetch("/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Ana Silva",
    email: "ana@test.com",
    password: "mypassword123"
  })
}).then(async r => console.log("POST /register duplicate", r.status, await r.text()))
```

```javascript
// Success: login and create the authentication cookie
fetch("/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "ana@test.com", password: "mypassword123" })
}).then(async r => console.log("POST /login success", r.status, await r.text()))
```

```javascript
// Unauthorized: wrong password
fetch("/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "ana@test.com", password: "wrong-password" })
}).then(async r => console.log("POST /login wrong credentials", r.status, await r.text()))
```

## Current user endpoints

```javascript
// Success: show claims for the logged-in user
fetch("/me")
  .then(async r => console.log("GET /me success", r.status, await r.text()))

// Forbidden shape: no authentication cookie; expected 401
// Use this after calling POST /logout.
fetch("/me")
  .then(async r => console.log("GET /me unauthenticated", r.status, await r.text()))
```

```javascript
// Success for any authenticated user
fetch("/users")
  .then(async r => console.log("GET /users", r.status, await r.text()))

// Success only for an admin
fetch("/admin-only")
  .then(async r => console.log("GET /admin-only", r.status, await r.text()))

// Forbidden for a basic user: expected 403
fetch("/admin-only")
  .then(async r => console.log("GET /admin-only forbidden", r.status, await r.text()))
```

```javascript
// Success: logout
fetch("/logout", { method: "POST" })
  .then(async r => console.log("POST /logout", r.status, await r.text()))
```

## Department endpoints

```javascript
// Success: list departments for any authenticated user
fetch("/departments")
  .then(async r => console.log("GET /departments", r.status, await r.text()))
```

```javascript
// Success: create a department as an admin
fetch("/departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Information Technology", code: "TI" })
}).then(async r => console.log("POST /departments success", r.status, await r.text()))
```

```javascript
// Validation error: missing name and code
fetch("/departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "", code: "" })
}).then(async r => console.log("POST /departments validation", r.status, await r.text()))
```

```javascript
// Conflict: create a department with an existing code
fetch("/departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Duplicate Technology", code: "TI" })
}).then(async r => console.log("POST /departments duplicate", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot create departments
fetch("/departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Forbidden Department", code: "NO" })
}).then(async r => console.log("POST /departments forbidden", r.status, await r.text()))
```

```javascript
// Success: assign a user to a department as an admin
// User and department IDs come from the claims/database, not from the current request context.
fetch("/user-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ userId: 1, departmentId: 1, accessType: "member" })
}).then(async r => console.log("POST /user-departments success", r.status, await r.text()))
```

```javascript
// Bad request: IDs do not reference existing records
fetch("/user-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ userId: 999, departmentId: 999, accessType: "member" })
}).then(async r => console.log("POST /user-departments bad request", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot assign departments
fetch("/user-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ userId: 1, departmentId: 1, accessType: "member" })
}).then(async r => console.log("POST /user-departments forbidden", r.status, await r.text()))
```

```javascript
// Success: list active departments of the currently logged-in user
fetch("/me/departments")
  .then(async r => console.log("GET /me/departments", r.status, await r.text()))
```

## POP endpoints

```javascript
// Success: admins see every POP; basic users see published POPs
// visible through an active department assignment
fetch("/pops")
  .then(async r => console.log("GET /pops", r.status, await r.text()))
```

```javascript
// Success: get an accessible POP by ID
fetch("/pops/1")
  .then(async r => console.log("GET /pops/1", r.status, await r.text()))
```

```javascript
// Not found: nonexistent or inaccessible POP
fetch("/pops/999")
  .then(async r => console.log("GET /pops/999", r.status, await r.text()))
```

```javascript
// Success: admin creates a POP
fetch("/pops", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Material Receiving",
    description: "Receiving process",
    filePath: "/files/pop1.pdf",
    version: "1.0",
    status: "draft"
  })
}).then(async r => console.log("POST /pops success", r.status, await r.text()))
```

```javascript
// Validation error: blank title
fetch("/pops", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "", status: "draft" })
}).then(async r => console.log("POST /pops title validation", r.status, await r.text()))
```

```javascript
// Validation error: invalid status
fetch("/pops", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Invalid status POP", status: "deleted" })
}).then(async r => console.log("POST /pops status validation", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot create POPs
fetch("/pops", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Forbidden POP", status: "draft" })
}).then(async r => console.log("POST /pops forbidden", r.status, await r.text()))
```

```javascript
// Success: admin updates the POP and updated_by/updated_at_utc are stored from the claims/clock
fetch("/pops/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Material Receiving - Updated",
    description: "Updated receiving process",
    filePath: "/files/pop1-v2.pdf",
    version: "2.0",
    status: "published"
  })
}).then(async r => console.log("PUT /pops/1 success", r.status, await r.text()))
```

```javascript
// Validation error: blank title and invalid status
fetch("/pops/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "", status: "invalid" })
}).then(async r => console.log("PUT /pops/1 validation", r.status, await r.text()))
```

```javascript
// Not found: POP does not exist
fetch("/pops/999", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Missing", description: "", filePath: "", version: "", status: "draft" })
}).then(async r => console.log("PUT /pops/999 not found", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot update POPs
fetch("/pops/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Forbidden update", description: "", filePath: "", version: "", status: "draft" })
}).then(async r => console.log("PUT /pops/1 forbidden", r.status, await r.text()))
```

```javascript
// Success: admin archives a POP
fetch("/pops/1/archive", { method: "POST" })
  .then(async r => console.log("POST /pops/1/archive success", r.status, await r.text()))
```

```javascript
// Not found: nonexistent POP
fetch("/pops/999/archive", { method: "POST" })
  .then(async r => console.log("POST /pops/999/archive not found", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot archive POPs
fetch("/pops/1/archive", { method: "POST" })
  .then(async r => console.log("POST /pops/1/archive forbidden", r.status, await r.text()))
```

## Link endpoints

```javascript
// Success, admin: list links
fetch("/links")
  .then(async r => console.log("GET /links success", r.status, await r.text()))

// Forbidden for basic users
fetch("/links")
  .then(async r => console.log("GET /links forbidden", r.status, await r.text()))
```

```javascript
// Success: admin creates a link
fetch("/links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/manual" })
}).then(async r => console.log("POST /links success", r.status, await r.text()))
```

```javascript
// Validation error: blank path
fetch("/links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "" })
}).then(async r => console.log("POST /links validation", r.status, await r.text()))
```

```javascript
// Conflict: link path already exists
fetch("/links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/manual" })
}).then(async r => console.log("POST /links duplicate", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot create links
fetch("/links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/forbidden" })
}).then(async r => console.log("POST /links forbidden", r.status, await r.text()))
```

```javascript
// Success: admin updates a link
fetch("/links/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/updated" })
}).then(async r => console.log("PUT /links/1 success", r.status, await r.text()))
```

```javascript
// Validation error: blank path
fetch("/links/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "" })
}).then(async r => console.log("PUT /links/1 validation", r.status, await r.text()))
```

```javascript
// Not found: link ID does not exist
fetch("/links/999", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/missing" })
}).then(async r => console.log("PUT /links/999 not found", r.status, await r.text()))
```

```javascript
// Conflict: new path is already used by another link
// Update links/1 after creating at least two different paths.
fetch("/links/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/manual" })
}).then(async r => console.log("PUT /links/1 duplicate", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot update links
fetch("/links/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ path: "https://example.com/forbidden" })
}).then(async r => console.log("PUT /links/1 forbidden", r.status, await r.text()))
```

## Phone-number endpoints

```javascript
// Success, admin: list phone numbers
fetch("/phones")
  .then(async r => console.log("GET /phones success", r.status, await r.text()))

// Forbidden for basic users
fetch("/phones")
  .then(async r => console.log("GET /phones forbidden", r.status, await r.text()))
```

```javascript
// Success: admin creates a phone number
fetch("/phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567890" })
}).then(async r => console.log("POST /phones success", r.status, await r.text()))
```

```javascript
// Validation error: blank phone number
fetch("/phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "" })
}).then(async r => console.log("POST /phones validation", r.status, await r.text()))
```

```javascript
// Conflict: phone number already exists
fetch("/phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567890" })
}).then(async r => console.log("POST /phones duplicate", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot create phone numbers
fetch("/phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551111111111" })
}).then(async r => console.log("POST /phones forbidden", r.status, await r.text()))
```

```javascript
// Success: admin updates a phone number
fetch("/phones/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567891" })
}).then(async r => console.log("PUT /phones/1 success", r.status, await r.text()))
```

```javascript
// Validation error: blank phone number
fetch("/phones/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "" })
}).then(async r => console.log("PUT /phones/1 validation", r.status, await r.text()))
```

```javascript
// Not found: phone ID does not exist
fetch("/phones/999", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567891" })
}).then(async r => console.log("PUT /phones/999 not found", r.status, await r.text()))
```

```javascript
// Conflict: number is already used by another phone record
fetch("/phones/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567890" })
}).then(async r => console.log("PUT /phones/1 duplicate", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot update phone numbers
fetch("/phones/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ phoneNumber: "+551234567891" })
}).then(async r => console.log("PUT /phones/1 forbidden", r.status, await r.text()))
```

## POP Link assignments and reader endpoints

```javascript
// Success: admin assigns a link to a POP
fetch("/pop-links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, linkId: 1 })
}).then(async r => console.log("POST /pop-links success", r.status, await r.text()))
```

```javascript
// Conflict: assignment already exists
fetch("/pop-links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, linkId: 1 })
}).then(async r => console.log("POST /pop-links duplicate", r.status, await r.text()))
```

```javascript
// Bad request: POP or link ID does not exist
fetch("/pop-links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 999, linkId: 999 })
}).then(async r => console.log("POST /pop-links bad request", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot assign links
fetch("/pop-links", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, linkId: 1 })
}).then(async r => console.log("POST /pop-links forbidden", r.status, await r.text()))
```

```javascript
// Success: authorized readers list links belonging to an accessible POP
fetch("/pops/1/links")
  .then(async r => console.log("GET /pops/1/links success", r.status, await r.text()))
```

```javascript
// Not found: inaccessible or nonexistent POP
fetch("/pops/999/links")
  .then(async r => console.log("GET /pops/999/links not found", r.status, await r.text()))
```

## POP phone assignments and reader endpoints

```javascript
// Success: admin assigns a phone number to a POP
fetch("/pop-phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, phoneId: 1 })
}).then(async r => console.log("POST /pop-phones success", r.status, await r.text()))
```

```javascript
// Conflict: assignment already exists
fetch("/pop-phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, phoneId: 1 })
}).then(async r => console.log("POST /pop-phones duplicate", r.status, await r.text()))
```

```javascript
// Bad request: POP or phone ID does not exist
fetch("/pop-phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 999, phoneId: 999 })
}).then(async r => console.log("POST /pop-phones bad request", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot assign phones
fetch("/pop-phones", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, phoneId: 1 })
}).then(async r => console.log("POST /pop-phones forbidden", r.status, await r.text()))
```

```javascript
// Success: authorized readers list phones belonging to an accessible POP
fetch("/pops/1/phones")
  .then(async r => console.log("GET /pops/1/phones success", r.status, await r.text()))
```

```javascript
// Not found: inaccessible or nonexistent POP
fetch("/pops/999/phones")
  .then(async r => console.log("GET /pops/999/phones not found", r.status, await r.text()))
```

## POP department assignments and reader endpoints

```javascript
// Success: admin assigns a department to a POP
fetch("/pop-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, departmentId: 1, accessType: "read" })
}).then(async r => console.log("POST /pop-departments success", r.status, await r.text()))
```

```javascript
// Conflict: assignment already exists
fetch("/pop-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, departmentId: 1, accessType: "read" })
}).then(async r => console.log("POST /pop-departments duplicate", r.status, await r.text()))
```

```javascript
// Bad request: POP or department ID does not exist
fetch("/pop-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 999, departmentId: 999, accessType: "read" })
}).then(async r => console.log("POST /pop-departments bad request", r.status, await r.text()))
```

```javascript
// Forbidden: basic users cannot assign departments
fetch("/pop-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ popId: 1, departmentId: 1, accessType: "read" })
}).then(async r => console.log("POST /pop-departments forbidden", r.status, await r.text()))
```

```javascript
// Success: authorized readers list departments assigned to an accessible POP
fetch("/pops/1/departments")
  .then(async r => console.log("GET /pops/1/departments success", r.status, await r.text()))
```

```javascript
// Not found: inaccessible or nonexistent POP
fetch("/pops/999/departments")
  .then(async r => console.log("GET /pops/999/departments not found", r.status, await r.text()))
```