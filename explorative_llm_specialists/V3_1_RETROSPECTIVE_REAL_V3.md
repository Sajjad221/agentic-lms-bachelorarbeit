# Retrospektiver Check des echten UC1-v3-Laufs

Die folgenden v3-Rejections beruhten auf Provenienz-Praefixen. v3.1 normalisiert diese auf den kanonischen Toolnamen:

- Course Agent: `verified_tool_outputs.read_modules` → `read_modules`
- Course Agent: `verified_tool_outputs.read_course` → `read_course`
- Course Agent: `verified_tool_outputs.read_groups` → `read_groups`
- Course Agent: `verified_tool_outputs.read_groups` → `read_groups`
- Course Agent: `verified_tool_outputs.read_groups` → `read_groups`
- Enrollment Agent: `verified_tool_outputs.read_groups` → `read_groups`
- Enrollment Agent: `verified_tool_outputs.read_users` → `read_users`
- Enrollment Agent: `verified_tool_outputs.read_modules` → `read_modules`
- Enrollment Agent: `verified_tool_outputs.read_groups` → `read_groups`

Gefundene praefixbedingte used_data-Rejections: **9**.

Hinweis: Dies ist nur ein retrospektiver Formatcheck. Der v3.1-Puffer bleibt getrennt vom offiziellen v4-Holdout.
