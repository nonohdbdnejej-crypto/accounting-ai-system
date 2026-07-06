-- ============================================
-- Migration: آلية "عكس القيد" بدل الحذف النهائي
-- نفّذ الملف ده مرة واحدة في Supabase SQL Editor
-- (بعد schema.sql - آمن تشغّله أكتر من مرة، مش هيكرر الأعمدة)
-- ============================================

alter table journal_entries
    add column if not exists is_reversed boolean not null default false;

alter table journal_entries
    add column if not exists reversed_by_entry_id uuid references journal_entries(id);

-- source_type كان بيقبل بس manual/invoice/payment ضمنيًا (من غير check constraint فعلي)
-- دلوقتي بنضيف 'reversal' كقيمة ممكنة لتوضيح إن القيد ده ناتج عن عكس قيد تاني
comment on column journal_entries.source_type is
    'manual | invoice | payment | expense | reversal';

create index if not exists idx_journal_entries_reversed on journal_entries(is_reversed);
