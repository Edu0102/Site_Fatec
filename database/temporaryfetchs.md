fetch("/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "ana@test.com", password: "mypassword123" })
}).then(async r => console.log(r.status, await r.text()))
-
fetch("/departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name: "Information Technology", code: "ti" })
}).then(async r => console.log(r.status, await r.text()))
-
fetch("/user-departments", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ userId: 1, departmentId: 1 })
}).then(async r => console.log(r.status, await r.text()))