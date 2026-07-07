create table notes (id uuid primary key, user_id uuid, body text);
alter table notes enable row level security;
