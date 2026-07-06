-- ============================================
-- Audit Log - تسجيل كل العمليات الحساسة
-- نفذ الملف ده بعد schema.sql مباشرة
-- ============================================

create table if not exists audit_log (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid references users(id),
    action text not null,          -- create, update, delete
    entity_type text not null,     -- invoice, journal_entry, payment, account, contact...
    entity_id uuid,
    details jsonb,
    ip_address text,
    created_at timestamptz default now()
);

create index if not exists idx_audit_entity on audit_log(entity_type, entity_id);
create index if not exists idx_audit_user on audit_log(user_id);
create index if not exists idx_audit_created on audit_log(created_at desc);
