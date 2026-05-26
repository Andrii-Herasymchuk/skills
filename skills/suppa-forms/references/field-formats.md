# Forms Field Formats & Data Conventions

## 1. IDs and Values

| Type | Format | Example |
|------|--------|---------|
| Form ID | integer | `123` |
| Entity ID | integer | `5` |
| User ID | integer | `42` |
| Field `id` in schema | UUID string | `"a1b2c3d4-e5f6-..."` |
| Field `name` in schema | camelCase string (unique) | `"firstName"` |
| Current user magic | `"$current-user"` | filter value |

---

## 2. Filter Object

```json
{
  "id": "f1",
  "field": "entity.name",
  "value": "Tasks",
  "comparator": "=",
  "disabled": false
}
```

### Comparators

| Comparator | Meaning |
|-----------|---------|
| `=` | Equals |
| `!=` | Not equals |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater or equal |
| `<=` | Less or equal |
| `like` | Contains (SQL LIKE) |
| `in` | Value in array |
| `not in` | Value not in array |
| `is null` | Is null |
| `is not null` | Is not null |
| `between` | Between two values |

---

## 3. TField (Form Schema Field Object)

Every field in `data.formShema[]` must have this shape:

```json
{
  "id": "uuid-string",
  "fieldId": "fieldName",
  "name": "fieldName",
  "type": "text",
  "label": {"en": "Field Label", "uk": "Назва поля"},
  "position": {
    "lg": {"x": 1, "y": 1},
    "sm": {"x": 1, "y": 1},
    "default": {"x": 1, "y": 1}
  },
  "columns": {"lg": {"container": 1}},
  "rows": {"lg": {"container": 1}}
}
```

**Labels** use ISO 639-1 codes: `en`, `uk`, `pl` (NOT locale codes like `en_US`).

**Position** uses 3 breakpoints: `lg` (desktop ≥1024px), `sm` (mobile <1024px), `default` (fallback).
The renderer resolves with fallback chain: lg → sm → default → raw object.

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string (UUID) | Unique field identifier |
| `fieldId` | string | Builder reference ID (usually same as name) |
| `name` | string | Unique field key (maps to entity property) |
| `type` | string | One of the field types (see below) |
| `label` | object | Multilingual labels: `{en: text, uk: text}` |
| `position` | object | Grid position `{lg: {x, y}, sm: {x, y}, default: {x, y}}` |
| `columns` | object | Column span `{lg: {container: N}}` |
| `rows` | object | Row span `{lg: {container: N}}` |

### Optional Properties (type-dependent)

| Property | Used By | Description |
|----------|---------|-------------|
| `inputType` | text | `"text"`, `"number"`, `"email"`, `"phone"`, `"password"` |
| `typeDate` | date | `"date"`, `"dateTime"`, `"time"` |
| `rules` | any | Array: `["required", "email", "numeric", "maxLength:100"]` |
| `items` | select, userSelect | Data source config (see §5) |
| `options` | select, files | Behavior config: `{multiple, valueIsObject}` |
| `schema` | group, flexGroup, tabs, steps, accordion | Nested field array |
| `columnsNumber` | group | Grid columns inside group (for children layout) |
| `content` | static | Text content for display |
| `tag` | static | HTML tag: `"h1"`, `"h2"`, `"h3"`, `"h4"`, `"hr"`, `"text"` |
| `color` | button | Button color: `"primary"`, `"success"`, `"danger"`, `"warning"` |
| `variant` | button | Button variant: `"elevated"`, `"flat"`, `"outlined"`, `"text"`, `"tonal"` |
| `rounded` | button | Border radius: `"md"`, `"sm"`, `"lg"`, `"xl"` |
| `fontWeight` | button | CSS font-weight: `"400"`, `"500"`, `"600"`, `"700"` |
| `icon` | button | Icon name string |
| `buttonLabel` | button | Multilingual button text `{en: text, uk: text}` |
| `submit` | button, static | `true` = submit on click, `false` = just a button |
| `widgetName` | widget | Component name: `"BaseChart"`, etc. |
| `props` | widget | Props passed to widget component |
| `src` | image, iFrameWidget | URL source |
| `mode` | checkbox | `"checkbox"` or `"checkboxgroup"` |
| `additionalRequestFields` | userSelect | Extra fields to fetch: `["avatar", "position"]` |
| `conditions` | any | Show/hide conditions (see §6) |
| `disabled` | any | Boolean — field is read-only |
| `hidden` | any | Boolean — field is not rendered |
| `visible` | any | Boolean — field visibility |
| `isFullHeight` | any | Boolean — field takes full available height |
| `placeholder` | text, textarea | Placeholder text (multilingual object) |
| `description` | any | Help text below field (multilingual object) |
| `containerPadding` | any | CSS padding for field container |
| `containerMargin` | any | CSS margin for field container |
| `xGap` | group | Horizontal gap between children |
| `yGap` | group | Vertical gap between children |
| `justifyContent` | flexGroup | Flex justify: `"start"`, `"center"`, `"end"`, `"space-between"` |
| `alignItems` | flexGroup | Flex align: `"start"`, `"center"`, `"end"`, `"stretch"` |

---

## 4. IFormConfig (Form Settings)

Stored in `data.formSettings`:

```json
{
  "id": 0,
  "size": "md",
  "type": "form",
  "method": "POST",
  "formKey": "",
  "endpoint": "",
  "entityId": "Tasks",
  "formType": "customForm",
  "columnsNumber": 2,
  "multilingual": false,
  "targetFormId": 96,
  "useTransaction": true,
  "showSubmitButton": false,
  "validateOnChange": true,
  "validateOnSubmit": true
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | integer | 0 | Internal settings ID |
| `size` | string | "md" | Form size: "sm", "md", "lg" |
| `type` | string | "form" | Internal type marker |
| `method` | string | "POST" | HTTP method for webforms |
| `formKey` | string | "" | Custom form key |
| `endpoint` | string | "" | Custom submission endpoint (webforms) |
| `entityId` | string | "" | Entity name this form is bound to |
| `formType` | string | "elementForm" | Form type (same as form.type) |
| `columnsNumber` | integer | 1 | Grid columns for top-level schema (1–12) |
| `multilingual` | boolean | false | Enable multilingual field values |
| `targetFormId` | integer | null | Reference form ID (customForm overriding elementForm) |
| `useTransaction` | boolean | true | Wrap save in transaction |
| `showSubmitButton` | boolean | false | Auto submit button at bottom |
| `validateOnSubmit` | boolean | true | Run validation on form submit |
| `validateOnChange` | boolean | true | Run validation on field change |

---

## 5. Items Config (for select / userSelect)

### Relation Select (entity dropdown)
```json
{
  "items": {
    "targetEntityId": 5,
    "targetEntityName": "Tasks",
    "targetValueField": "id",
    "targetLabelField": "title"
  },
  "options": {
    "valueIsObject": true,
    "usePreLoadItemsFunction": true,
    "multiple": false
  }
}
```

### User Select
```json
{
  "items": {
    "targetEntityName": "Users",
    "targetValueField": "id",
    "targetLabelField": "fullName"
  },
  "options": {"multiple": false},
  "additionalRequestFields": ["firstName", "lastName", "fullName", "avatar", "position"]
}
```

### Enum Select
```json
{
  "items": {
    "enum_id": "Tasks.priority",
    "targetType": "internal",
    "targetEntityName": "Enums",
    "targetValueField": "id",
    "targetLabelField": "title"
  },
  "options": {"valueIsObject": true, "multiple": false}
}
```

---

## 6. Conditions (Show/Hide/Disable)

Field-level conditions for dynamic visibility:

```json
{
  "conditions": [
    {
      "field": "status",
      "comparator": "=",
      "value": "active",
      "action": "show"
    }
  ]
}
```

| Property | Description |
|----------|-------------|
| `field` | Name of another field to check |
| `comparator` | `=`, `!=`, `in`, `not in`, `is null`, `is not null` |
| `value` | Value to compare against |
| `action` | `"show"`, `"hide"`, `"disable"`, `"enable"` |

---

## 7. Form Module Code (formModul)

A JavaScript string stored in `data.formModul`. Runs as a Vue composition-like module:

```javascript
export default {
  mounted(ctx) {
    // ctx.form — form instance
    // ctx.formData — reactive form values
    // ctx.entityData — current entity record
    // ctx.emitter — event bus
  },
  methods: {
    onFieldChange(ctx, fieldName, value) {
      // React to field changes
    },
    onSubmit(ctx) {
      // Custom submit logic
    }
  }
}
```

---

## 8. Form Types

| Type | Purpose |
|------|---------|
| `elementForm` | Entity record form (view/edit) |
| `customForm` | Standalone form (no entity binding) |
| `dashboard` | Dashboard layout with widgets/charts |
| `webform` | Public-facing web form |
| `listForm` | List/table view form |

---

## 9. Validation Rules

Rules are string arrays in the `rules` property:

| Rule | Description |
|------|-------------|
| `required` | Field must have a value |
| `email` | Must be valid email |
| `numeric` | Must be a number |
| `phone` | Must be valid phone |
| `maxLength:N` | Maximum character length |
| `minLength:N` | Minimum character length |
| `max:N` | Maximum numeric value |
| `min:N` | Minimum numeric value |
| `decimalPlaces:N` | Maximum decimal places |
| `isOnlyPositive` | Must be positive number |
| `url` | Must be valid URL |
| `regex:/pattern/` | Custom regex validation |

---

## 10. Position & Layout Grid

Forms use a CSS Grid layout. Position is 1-based:

```
columnsNumber = 2

Row 1: [field x=1] [field x=2]
Row 2: [field x=1, cols=2 (full width)]
Row 3: [field x=1] [field x=2]
```

- `position.lg.x` — column (1-based, max = columnsNumber)
- `position.lg.y` — row (1-based, auto-increments)
- `columns.lg.container` — how many columns the field spans
- `rows.lg.container` — how many rows the field spans (usually 1)

---

## 11. Response Shape

### Search response
Always an array:
```json
[{...}, {...}, ...]
```

### Select response
Single object or array with one element.

### Insert response (with `returning`)
Array with inserted records:
```json
[{"id": 200, "name": "New Form", "type": "elementForm"}]
```

### Update response
Varies — often `{"affected": 1}` or the updated record.

---

## 12. orderBy Format

```json
[
  {"field": "id", "order": "desc"},
  {"field": "name", "order": "asc"}
]
```

`order` values: `"asc"`, `"desc"`.
