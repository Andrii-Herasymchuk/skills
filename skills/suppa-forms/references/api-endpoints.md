# Forms API — Endpoint Reference

Base URL: `https://modern.suppa.me`
Entity: `Forms`

All requests require:
```
Authorization: Bearer <TOKEN>
Content-Type: application/json; charset=UTF-8
x-current-language: en
x-timezone: Europe/Kyiv
x-view-mode: view
```

---

## 1. Search Forms

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conditions": {
      "operator": "and",
      "filters": [
        {"id": "f1", "field": "entity.name", "value": "Tasks", "comparator": "=", "disabled": false}
      ]
    },
    "fields": {"id": true, "name": true, "type": true, "alias": true, "entity": {"id": true, "name": true}},
    "limit": 50,
    "offset": 0,
    "orderBy": [{"field": "id", "order": "desc"}],
    "searchValue": "",
    "getAccessByFields": true,
    "includeDeletedRelations": false
  }'
```

**Response** (array):
```json
[
  {"id": 123, "name": "Task Details", "type": "elementForm", "alias": "task-details", "entity": {"id": 5, "name": "Tasks"}},
  {"id": 124, "name": "Task Board", "type": "dashboard", "alias": null, "entity": {"id": 5, "name": "Tasks"}}
]
```

---

## 2. Select (Get) Single Form

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/select" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conditions": {
      "operator": "and",
      "filters": [
        {"id": "f1", "field": "id", "value": 123, "comparator": "=", "disabled": false}
      ]
    },
    "fields": {"id": true, "name": true, "type": true, "alias": true, "isPublic": true, "data": true, "entity": {"id": true, "name": true}, "lockedBy": {"id": true, "firstName": true, "lastName": true}},
    "limit": 1,
    "offset": 0,
    "orderBy": [{"field": "id", "order": "asc"}],
    "getAccessByFields": true,
    "includeDeletedRelations": false
  }'
```

**Response** (single object or array with one item):
```json
{
  "id": 123,
  "name": "Task Details",
  "type": "elementForm",
  "alias": "task-details",
  "isPublic": false,
  "entity": {"id": 5, "name": "Tasks"},
  "lockedBy": null,
  "data": {
    "formShema": [ ... ],
    "formSettings": { ... },
    "formModul": "export default { ... }"
  }
}
```

---

## 3. Insert (Create) Form

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/insert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": [{
      "name": "My New Form",
      "type": "elementForm",
      "isPublic": false,
      "entity": {"id": 5},
      "data": {
        "formShema": [
          {
            "id": "uuid-1",
            "name": "title",
            "type": "text",
            "label": {"en_US": "Title"},
            "inputType": "text",
            "rules": ["required"],
            "position": {"lg": {"x": 1, "y": 1}},
            "columns": {"lg": {"container": 1}},
            "rows": {"lg": {"container": 1}}
          }
        ],
        "formSettings": {
          "columnsNumber": 1,
          "showSubmitButton": false,
          "validateOnSubmit": true,
          "validateOnChange": true,
          "size": "md"
        },
        "formModul": null
      }
    }],
    "returning": {"id": true, "name": true, "type": true}
  }'
```

**Response**:
```json
[{"id": 200, "name": "My New Form", "type": "elementForm"}]
```

---

## 4. Update Form

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": [{
      "name": "Updated Name",
      "data": {
        "formShema": [ ... ],
        "formSettings": {"columnsNumber": 2},
        "formModul": "export default { mounted() {} }"
      }
    }],
    "conditions": {
      "operator": "and",
      "filters": [
        {"id": "f1", "field": "id", "value": 200, "comparator": "=", "disabled": false}
      ]
    }
  }'
```

---

## 5. Lock Form (set lockedBy)

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": [{"lockedBy": {"id": 42}}],
    "conditions": {"operator": "and", "filters": [{"id": "f1", "field": "id", "value": 200, "comparator": "=", "disabled": false}]}
  }'
```

## 6. Unlock Form (clear lockedBy)

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Forms/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": [{"lockedBy": null}],
    "conditions": {"operator": "and", "filters": [{"id": "f1", "field": "id", "value": 200, "comparator": "=", "disabled": false}]}
  }'
```

---

## 7. Get Entity Schema (for field generation)

```bash
curl -X GET "https://modern.suppa.me/api/core/schema/Tasks" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (varies by entity — typically object with `properties` array):
```json
{
  "id": 5,
  "name": "Tasks",
  "properties": [
    {"name": "title", "type": "String", "title": {"en_US": "Title"}, "required": "always"},
    {"name": "assignedTo", "type": "relation", "relation": {"relation_target_entity_name": "Users", "relation_type": "many-to-one", "representativeField": "fullName"}},
    {"name": "priority", "type": "enum", "custom_enum": {"enum_id": "Tasks.priority"}},
    {"name": "dueDate", "type": "DateTime"},
    {"name": "description", "type": "String", "sub_type": "html_text"}
  ]
}
```

---

## 8. Get Current User

```bash
curl -X POST "https://modern.suppa.me/api/core/data/Users/select?markAsView=false" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {"id": true, "firstName": true, "lastName": true, "fullName": true, "position": true, "avatar": {"id": true, "fileName": true}, "roles": {"id": true, "name": true}},
    "conditions": {"operator": "and", "filters": [{"id": "f1", "field": "id", "value": "$current-user", "comparator": "=", "disabled": false}]},
    "limit": 1,
    "getAccessByFields": true,
    "includeDeletedRelations": false
  }'
```

---

## Notes

- **Integer IDs**: Form IDs, entity IDs, and user IDs are integers.
- **`$current-user`**: Magic value in filter to reference the authenticated user.
- **Field projection**: Use `{"fieldName": true}` for scalar fields. Use `{"relation": {"id": true, "name": true}}` for relations.
- **Entity reference**: When assigning entity to a form, send `{"id": <entityId>}` (integer).
- **`data` field**: The `data` column is a JSON column containing `formShema`, `formSettings`, and `formModul`.
