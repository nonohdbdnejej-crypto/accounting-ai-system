-- ============================================
-- نظام محاسبة احترافي - قيد مزدوج (Double-Entry)
-- شغّل الملف ده في Supabase SQL Editor
-- ============================================

create extension if not exists "uuid-ossp";

-- ---------- المستخدمين ----------
create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    username text unique not null,
    password_hash text not null,
    full_name text,
    email text,
    phone text,
    role text not null default 'accountant' check (role in ('admin','accountant','viewer')),
    is_active boolean default true,
    created_at timestamptz default now()
);

-- ---------- دليل الحسابات ----------
create table if not exists accounts (
    id uuid primary key default uuid_generate_v4(),
    code text unique not null,
    name text not null,
    type text not null check (type in ('asset','liability','equity','revenue','expense')),
    parent_id uuid references accounts(id) on delete set null,
    is_active boolean default true,
    created_at timestamptz default now()
);

-- ---------- القيود اليومية (رأس القيد) ----------
create table if not exists journal_entries (
    id uuid primary key default uuid_generate_v4(),
    entry_number serial,
    entry_date date not null default current_date,
    description text,
    reference text,
    source_type text default 'manual', -- manual, invoice, payment, expense, reversal
    source_id uuid,
    created_by uuid references users(id),
    is_posted boolean default true,
    is_reversed boolean not null default false,
    reversed_by_entry_id uuid references journal_entries(id),
    created_at timestamptz default now()
);

-- ---------- بنود القيد (مدين/دائن) ----------
create table if not exists journal_entry_lines (
    id uuid primary key default uuid_generate_v4(),
    entry_id uuid references journal_entries(id) on delete cascade,
    account_id uuid references accounts(id),
    debit numeric(14,2) not null default 0,
    credit numeric(14,2) not null default 0,
    description text,
    line_order int default 0,
    check (debit >= 0 and credit >= 0),
    check (not (debit > 0 and credit > 0))
);

-- ---------- العملاء والموردين ----------
create table if not exists contacts (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    type text not null check (type in ('client','supplier','both')),
    phone text,
    email text,
    address text,
    tax_number text,
    account_id uuid references accounts(id),
    opening_balance numeric(14,2) default 0,
    created_at timestamptz default now()
);

-- ---------- المنتجات / المخزون ----------
create table if not exists products (
    id uuid primary key default uuid_generate_v4(),
    sku text unique,
    name text not null,
    unit text default 'قطعة',
    cost_price numeric(14,2) default 0,
    sale_price numeric(14,2) default 0,
    quantity numeric(14,2) default 0,
    reorder_level numeric(14,2) default 0,
    is_active boolean default true,
    created_at timestamptz default now()
);

-- ---------- الفواتير (رأس الفاتورة) ----------
create table if not exists invoices (
    id uuid primary key default uuid_generate_v4(),
    invoice_number serial,
    type text not null check (type in ('sale','purchase')),
    contact_id uuid references contacts(id),
    invoice_date date not null default current_date,
    due_date date,
    status text not null default 'draft' check (status in ('draft','confirmed','paid','cancelled')),
    subtotal numeric(14,2) default 0,
    tax_total numeric(14,2) default 0,
    total numeric(14,2) default 0,
    journal_entry_id uuid references journal_entries(id),
    notes text,
    created_by uuid references users(id),
    created_at timestamptz default now()
);

-- ---------- بنود الفاتورة ----------
create table if not exists invoice_items (
    id uuid primary key default uuid_generate_v4(),
    invoice_id uuid references invoices(id) on delete cascade,
    product_id uuid references products(id),
    description text,
    quantity numeric(14,2) not null default 1,
    unit_price numeric(14,2) not null default 0,
    tax_rate numeric(5,2) default 0,
    total numeric(14,2) not null default 0
);

-- ---------- المقبوضات والمدفوعات ----------
create table if not exists payments (
    id uuid primary key default uuid_generate_v4(),
    payment_number serial,
    type text not null check (type in ('receipt','payment')),
    contact_id uuid references contacts(id),
    invoice_id uuid references invoices(id),
    amount numeric(14,2) not null,
    payment_date date not null default current_date,
    method text default 'cash' check (method in ('cash','bank','check')),
    cash_account_id uuid references accounts(id),
    journal_entry_id uuid references journal_entries(id),
    notes text,
    created_by uuid references users(id),
    created_at timestamptz default now()
);

-- ---------- فيوهات مساعدة للتقارير ----------

-- رصيد كل حساب (مجموع مدين - دائن حسب طبيعة الحساب)
create or replace view account_balances as
select
    a.id,
    a.code,
    a.name,
    a.type,
    coalesce(sum(l.debit), 0) as total_debit,
    coalesce(sum(l.credit), 0) as total_credit,
    case
        when a.type in ('asset','expense') then coalesce(sum(l.debit),0) - coalesce(sum(l.credit),0)
        else coalesce(sum(l.credit),0) - coalesce(sum(l.debit),0)
    end as balance
from accounts a
left join journal_entry_lines l on l.account_id = a.id
group by a.id, a.code, a.name, a.type;

-- ميزان المراجعة
create or replace view trial_balance as
select code, name, type, total_debit, total_credit
from account_balances
order by code;

-- الفهارس
create index if not exists idx_jel_entry on journal_entry_lines(entry_id);
create index if not exists idx_jel_account on journal_entry_lines(account_id);
create index if not exists idx_invoices_contact on invoices(contact_id);
create index if not exists idx_invoice_items_invoice on invoice_items(invoice_id);
create index if not exists idx_users_username on users(username);
