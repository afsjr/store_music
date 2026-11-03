-- Schema do agente de atendimento da Empório da Música.
-- Aplicar com: psql "$SUPABASE_DB_URL" -f supabase/migrations/001_schema.sql

create extension if not exists pg_trgm;
create extension if not exists unaccent;

create table if not exists categories (
    category_id integer primary key,
    name text not null,
    description text not null default ''
);

create table if not exists products (
    product_id integer primary key,
    name text not null,
    price_brl numeric(10,2) not null check (price_brl >= 0),
    category_id integer not null references categories(category_id),
    description text not null default '',
    stock_quantity integer not null default 0 check (stock_quantity >= 0),
    status text not null default 'active'
        check (status in ('active', 'discontinued', 'coming_soon')),
    specs jsonb not null default '{}'::jsonb,
    created_at date,
    search_vector tsvector generated always as (
        to_tsvector(
            'portuguese',
            coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(specs::text, '')
        )
    ) stored
);

create table if not exists customers (
    customer_id integer primary key,
    name text not null,
    phone text not null,
    email text not null,
    city text not null
);

create table if not exists orders (
    order_id integer primary key,
    customer_id integer not null references customers(customer_id),
    order_date date not null,
    status text not null
        check (status in ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_brl numeric(10,2) not null check (total_brl >= 0),
    payment_method text not null,
    tracking_code text,
    estimated_delivery date,
    notes text
);

create table if not exists order_items (
    order_id integer not null references orders(order_id) on delete cascade,
    product_id integer not null references products(product_id),
    quantity integer not null check (quantity > 0),
    primary key (order_id, product_id)
);

create table if not exists promotions (
    promotion_id integer primary key,
    product_id integer not null references products(product_id),
    discount_percent numeric(5,2) not null check (discount_percent between 0 and 100),
    description text not null default '',
    is_active boolean not null default false
);

create table if not exists conversations (
    id uuid primary key default gen_random_uuid(),
    session_id text not null unique,
    customer_id integer references customers(customer_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists messages (
    id bigserial primary key,
    conversation_id uuid not null references conversations(id) on delete cascade,
    role text not null check (role in ('user', 'assistant', 'tool', 'system')),
    content text not null,
    tool_calls jsonb not null default '[]'::jsonb,
    citations jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists handoffs (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    reason text not null,
    summary text not null,
    status text not null default 'aberto'
        check (status in ('aberto', 'em_atendimento', 'resolvido')),
    created_at timestamptz not null default now(),
    resolved_at timestamptz
);

create table if not exists policy_documents (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    version text not null,
    source_path text not null,
    indexed_at timestamptz not null default now()
);

create table if not exists policy_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references policy_documents(id) on delete cascade,
    section text not null,
    page integer not null,
    content text not null,
    tokens integer not null default 0 check (tokens >= 0)
);

create table if not exists store_info (
    key text primary key,
    value text not null,
    source_section text not null,
    source_page integer not null
);

create table if not exists ingestion_runs (
    id uuid primary key default gen_random_uuid(),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null default 'running'
        check (status in ('running', 'success', 'failed')),
    counts jsonb not null default '{}'::jsonb,
    report_path text
);

create or replace view product_offers as
select
    p.product_id,
    p.name,
    p.price_brl,
    p.stock_quantity,
    p.status,
    pr.promotion_id,
    pr.discount_percent,
    pr.description as promotion_description,
    case
        when pr.promotion_id is not null
            then round(p.price_brl * (1 - pr.discount_percent / 100.0), 2)
        else p.price_brl
    end as effective_price,
    (pr.promotion_id is not null) as has_active_promotion
from products p
left join lateral (
    select *
    from promotions p2
    where p2.product_id = p.product_id and p2.is_active
    order by p2.discount_percent desc
    limit 1
) pr on true;

create index if not exists idx_products_category on products(category_id);
create index if not exists idx_products_price on products(price_brl);
create index if not exists idx_products_status on products(status);
create index if not exists idx_products_stock on products(stock_quantity);
create index if not exists idx_products_search on products using gin(search_vector);
create index if not exists idx_products_name_trgm on products using gin(name gin_trgm_ops);
create index if not exists idx_orders_customer on orders(customer_id);
create index if not exists idx_orders_status on orders(status);
create index if not exists idx_order_items_order on order_items(order_id);
create index if not exists idx_promotions_product on promotions(product_id, is_active);
create index if not exists idx_conversations_session on conversations(session_id);
create index if not exists idx_messages_conversation on messages(conversation_id, created_at);
create index if not exists idx_handoffs_conversation on handoffs(conversation_id);

insert into store_info (key, value, source_section, source_page) values
    ('endereco', 'Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333', '1.2', 2),
    ('telefone', '(67) 3341-4444', '1.2', 2),
    ('whatsapp', '(67) 3321-4500', '7', 6),
    ('email', 'contato@emporiodamusica.com.br', '1.2', 2),
    ('horario_segunda_sexta', '09:00 às 18:00', '2', 2),
    ('horario_sabado', '09:00 às 13:00', '2', 2),
    ('horario_domingo_feriados', 'Fechado', '2', 2)
on conflict (key) do update set
    value = excluded.value,
    source_section = excluded.source_section,
    source_page = excluded.source_page;

alter table categories enable row level security;
alter table products enable row level security;
alter table customers enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;
alter table promotions enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table handoffs enable row level security;
alter table policy_documents enable row level security;
alter table policy_chunks enable row level security;
alter table store_info enable row level security;
alter table ingestion_runs enable row level security;

-- O backend acessa o banco com credencial de servidor. Nenhuma policy para anon
-- é criada de propósito: a UI fala apenas com o FastAPI, nunca direto com o Supabase.
