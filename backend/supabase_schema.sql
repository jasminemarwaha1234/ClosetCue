-- The app's tables in Supabase (PLAN.md section 4). Run this once in the Supabase dashboard:
-- SQL Editor -> New query -> paste -> Run. Running it again is safe.
--
-- Who can read what: the phone signs in anonymously but never reads these tables itself.
-- Every read and write goes through the backend with the secret key, which bypasses row
-- level security. So RLS is on with no policies, and the publishable key the app ships
-- (the anon and authenticated roles) can't read or write anything here.
--
-- Every row belongs to an auth user and is deleted with them ("on delete cascade"), so
-- DELETE /me removing the user removes their profile, feedback and mandates too.

-- One style profile per user: the StyleProfile from backend/schemas.py, closet included.
create table if not exists public.profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  profile jsonb not null,
  updated_at timestamptz not null default now()
);

-- Blind A/B choices from the Rate screen. Exports straight to the DPO dataset: the prompt
-- is `request` plus the profile, and the chosen side's model is a_model or b_model.
create table if not exists public.feedback (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  pair_id text not null,
  choice text not null check (choice in ('a', 'b')),
  pair jsonb not null, -- the RatePair shown: request, profile_summary, a, b
  a_model text not null, -- which model made outfit a; never sent to the app
  b_model text not null,
  created_at timestamptz not null default now(),
  unique (user_id, pair_id) -- rating the same pair twice keeps one answer
);

-- Spending mandates for checkout (PLAN.md section 8). Amounts in dollars.
create table if not exists public.mandates (
  id text primary key, -- mandate_<...>, also sent to the app
  user_id uuid not null references auth.users (id) on delete cascade,
  "limit" numeric(10, 2) not null check ("limit" > 0),
  spent numeric(10, 2) not null default 0 check (spent >= 0),
  expires_at timestamptz not null,
  card_id text, -- Stripe Issuing's ic_...; null in the simulated fallback
  card_label text not null, -- "Visa •••• 4242, agent card"
  created_at timestamptz not null default now()
);

create index if not exists feedback_user_id on public.feedback (user_id);
create index if not exists mandates_user_id on public.mandates (user_id);

alter table public.profiles enable row level security;
alter table public.feedback enable row level security;
alter table public.mandates enable row level security;

-- Belt and braces: the app's roles get no table rights at all, only the backend does.
revoke all on public.profiles, public.feedback, public.mandates from anon, authenticated;
grant all on public.profiles, public.feedback, public.mandates to service_role;
grant usage, select on sequence public.feedback_id_seq to service_role;
