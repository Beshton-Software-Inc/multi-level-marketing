--
-- PostgreSQL database dump
--

\restrict VxOdibSFgxrIa0Y0EePzzt9UmR92C2UQErJWhEBOoAPyDLnwGF0cWLeABZHO6wx

-- Dumped from database version 18.4 (Debian 18.4-1.pgdg13+1)
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: affiliates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.affiliates (
    id integer NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    referral_code character varying NOT NULL,
    referred_by_id integer,
    status character varying,
    total_earnings numeric(10,2),
    is_admin boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.affiliates OWNER TO postgres;

--
-- Name: affiliates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.affiliates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.affiliates_id_seq OWNER TO postgres;

--
-- Name: affiliates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.affiliates_id_seq OWNED BY public.affiliates.id;


--
-- Name: commissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.commissions (
    id integer NOT NULL,
    earner_id integer NOT NULL,
    source_id integer,
    amount numeric(10,2) NOT NULL,
    tier integer NOT NULL,
    description character varying,
    status character varying,
    created_at timestamp with time zone DEFAULT now(),
    subscription_amount numeric(10,2),
    commission_rate numeric(6,4),
    team_allocation_pct numeric(5,2)
);


ALTER TABLE public.commissions OWNER TO postgres;

--
-- Name: commissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.commissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.commissions_id_seq OWNER TO postgres;

--
-- Name: commissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.commissions_id_seq OWNED BY public.commissions.id;


--
-- Name: payout_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payout_requests (
    id integer NOT NULL,
    affiliate_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    status character varying,
    payment_method character varying,
    payment_details character varying,
    admin_notes character varying,
    created_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone
);


ALTER TABLE public.payout_requests OWNER TO postgres;

--
-- Name: payout_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payout_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payout_requests_id_seq OWNER TO postgres;

--
-- Name: payout_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payout_requests_id_seq OWNED BY public.payout_requests.id;


--
-- Name: sales_teams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sales_teams (
    id integer NOT NULL,
    name character varying NOT NULL,
    referral_prefix character varying(8) NOT NULL,
    commission_rate numeric(5,2) NOT NULL,
    is_active boolean,
    notes character varying,
    created_at timestamp with time zone DEFAULT now(),
    commission_mode character varying DEFAULT 'default'::character varying NOT NULL,
    unassigned_policy character varying DEFAULT 'compress'::character varying NOT NULL,
    custom_rate_l1 numeric(5,2),
    custom_rate_l2 numeric(5,2),
    custom_rate_l3 numeric(5,2),
    custom_rate_l4 numeric(5,2),
    custom_rate_l5 numeric(5,2),
    custom_rate_l6 numeric(5,2),
    custom_rate_l7 numeric(5,2)
);


ALTER TABLE public.sales_teams OWNER TO postgres;

--
-- Name: sales_teams_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sales_teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_teams_id_seq OWNER TO postgres;

--
-- Name: sales_teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sales_teams_id_seq OWNED BY public.sales_teams.id;


--
-- Name: team_memberships; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_memberships (
    id integer NOT NULL,
    team_id integer NOT NULL,
    affiliate_id integer NOT NULL,
    role character varying,
    joined_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.team_memberships OWNER TO postgres;

--
-- Name: team_memberships_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_memberships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_memberships_id_seq OWNER TO postgres;

--
-- Name: team_memberships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_memberships_id_seq OWNED BY public.team_memberships.id;


--
-- Name: webhook_failures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webhook_failures (
    id integer NOT NULL,
    subscription_id character varying NOT NULL,
    referral_code character varying NOT NULL,
    customer_email character varying NOT NULL,
    payload character varying NOT NULL,
    error_message character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    resolved boolean,
    resolved_at timestamp with time zone
);


ALTER TABLE public.webhook_failures OWNER TO postgres;

--
-- Name: webhook_failures_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.webhook_failures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webhook_failures_id_seq OWNER TO postgres;

--
-- Name: webhook_failures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.webhook_failures_id_seq OWNED BY public.webhook_failures.id;


--
-- Name: affiliates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.affiliates ALTER COLUMN id SET DEFAULT nextval('public.affiliates_id_seq'::regclass);


--
-- Name: commissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commissions ALTER COLUMN id SET DEFAULT nextval('public.commissions_id_seq'::regclass);


--
-- Name: payout_requests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_requests ALTER COLUMN id SET DEFAULT nextval('public.payout_requests_id_seq'::regclass);


--
-- Name: sales_teams id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales_teams ALTER COLUMN id SET DEFAULT nextval('public.sales_teams_id_seq'::regclass);


--
-- Name: team_memberships id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_memberships ALTER COLUMN id SET DEFAULT nextval('public.team_memberships_id_seq'::regclass);


--
-- Name: webhook_failures id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webhook_failures ALTER COLUMN id SET DEFAULT nextval('public.webhook_failures_id_seq'::regclass);


--
-- Data for Name: affiliates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.affiliates (id, name, email, password_hash, referral_code, referred_by_id, status, total_earnings, is_admin, created_at) FROM stdin;
1	Dave Wang	wang.dave@gmail.com	$2b$12$WeXhiu38nfgdQTG2J1o9cO89RNtf7FFBkGlJlFUdnn4BFg325fxr6	RQUS9GCV	\N	active	0.00	f	2026-06-23 20:40:12.847485+00
2	Admin	admin@winwinlaw.com	$2b$12$BzaQ86T6bN83lUJIYC45LOVpwELi.dxXbHlEkSTZsGV4kRvO2Z8r.	1RFQIZ81	\N	active	0.00	t	2026-06-23 23:24:44.084732+00
3	Test Affiliate	affiliate@test.com	$2b$12$e.ecZ5wMFN6uPEd8.e/HP.C4KPZx4v6/126t.YCV1Q8GAZTjAIqkG	XY0OCMVA	\N	active	0.00	f	2026-06-23 23:54:15.047301+00
4	Affiliate A	aff.a@test.com	$2b$12$MPzFQfvLkvN1sGZA/dHL4.1Cx3ImM0I4oEzSmjF8PTLajsIff4cP6	F3E17CXZ	\N	active	105.00	f	2026-06-23 23:57:00.81682+00
5	Affiliate B	aff.b@test.com	$2b$12$ZFGpvOC9BaAJNDMoOr8AGetbKtbs/eQwI4MPNDVKZ7JqgJATSP5ea	WWLTEST1	4	active	0.00	f	2026-06-23 23:57:01.16011+00
\.


--
-- Data for Name: commissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.commissions (id, earner_id, source_id, amount, tier, description, status, created_at, subscription_amount, commission_rate, team_allocation_pct) FROM stdin;
1	4	5	10.00	1	Level 1 commission from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.2000	50.00
2	4	5	2.50	2	Level 2 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.0500	50.00
3	4	5	2.50	3	Level 3 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.0500	50.00
4	4	5	1.50	4	Level 4 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.0300	50.00
5	4	5	1.00	5	Level 5 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.0200	50.00
6	4	5	2.50	6	Level 6 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.0500	50.00
7	4	5	5.00	7	Level 7 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:01.689819+00	100.00	0.1000	50.00
8	4	5	8.00	1	Level 1 commission from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.2000	40.00
9	4	5	2.00	2	Level 2 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.0500	40.00
10	4	5	2.00	3	Level 3 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.0500	40.00
11	4	5	1.20	4	Level 4 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.0300	40.00
12	4	5	0.80	5	Level 5 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.0200	40.00
13	4	5	2.00	6	Level 6 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.0500	40.00
14	4	5	4.00	7	Level 7 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-23 23:57:56.715974+00	100.00	0.1000	40.00
15	4	5	8.00	1	Level 1 commission from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.2000	40.00
16	4	5	2.00	2	Level 2 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.0500	40.00
17	4	5	2.00	3	Level 3 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.0500	40.00
18	4	5	1.20	4	Level 4 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.0300	40.00
19	4	5	0.80	5	Level 5 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.0200	40.00
20	4	5	2.00	6	Level 6 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.0500	40.00
21	4	5	4.00	7	Level 7 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.691642+00	100.00	0.1000	40.00
22	4	5	8.00	1	Level 1 commission from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.2000	40.00
23	4	5	2.00	2	Level 2 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.0500	40.00
24	4	5	2.00	3	Level 3 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.0500	40.00
25	4	5	1.20	4	Level 4 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.0300	40.00
26	4	5	0.80	5	Level 5 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.0200	40.00
27	4	5	2.00	6	Level 6 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.0500	40.00
28	4	5	4.00	7	Level 7 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:21.857651+00	100.00	0.1000	40.00
29	4	5	8.00	1	Level 1 commission from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.2000	40.00
30	4	5	2.00	2	Level 2 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.0500	40.00
31	4	5	2.00	3	Level 3 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.0500	40.00
32	4	5	1.20	4	Level 4 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.0300	40.00
33	4	5	0.80	5	Level 5 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.0200	40.00
34	4	5	2.00	6	Level 6 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.0500	40.00
35	4	5	4.00	7	Level 7 commission (compressed to L1) from Affiliate B's subscription	pending	2026-06-24 00:09:22.001384+00	100.00	0.1000	40.00
\.


--
-- Data for Name: payout_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payout_requests (id, affiliate_id, amount, status, payment_method, payment_details, admin_notes, created_at, processed_at) FROM stdin;
\.


--
-- Data for Name: sales_teams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sales_teams (id, name, referral_prefix, commission_rate, is_active, notes, created_at, commission_mode, unassigned_policy, custom_rate_l1, custom_rate_l2, custom_rate_l3, custom_rate_l4, custom_rate_l5, custom_rate_l6, custom_rate_l7) FROM stdin;
1	Team A	TEAMA	40.00	t	\N	2026-06-23 23:53:51.897382+00	default	compress	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: team_memberships; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_memberships (id, team_id, affiliate_id, role, joined_at) FROM stdin;
1	1	3	member	2026-06-23 23:54:15.46094+00
2	1	5	member	2026-06-23 23:57:01.549825+00
\.


--
-- Data for Name: webhook_failures; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.webhook_failures (id, subscription_id, referral_code, customer_email, payload, error_message, created_at, resolved, resolved_at) FROM stdin;
\.


--
-- Name: affiliates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.affiliates_id_seq', 5, true);


--
-- Name: commissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.commissions_id_seq', 35, true);


--
-- Name: payout_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payout_requests_id_seq', 1, false);


--
-- Name: sales_teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sales_teams_id_seq', 1, true);


--
-- Name: team_memberships_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_memberships_id_seq', 2, true);


--
-- Name: webhook_failures_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.webhook_failures_id_seq', 1, false);


--
-- Name: affiliates affiliates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.affiliates
    ADD CONSTRAINT affiliates_pkey PRIMARY KEY (id);


--
-- Name: commissions commissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commissions
    ADD CONSTRAINT commissions_pkey PRIMARY KEY (id);


--
-- Name: payout_requests payout_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_requests
    ADD CONSTRAINT payout_requests_pkey PRIMARY KEY (id);


--
-- Name: sales_teams sales_teams_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales_teams
    ADD CONSTRAINT sales_teams_name_key UNIQUE (name);


--
-- Name: sales_teams sales_teams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales_teams
    ADD CONSTRAINT sales_teams_pkey PRIMARY KEY (id);


--
-- Name: sales_teams sales_teams_referral_prefix_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales_teams
    ADD CONSTRAINT sales_teams_referral_prefix_key UNIQUE (referral_prefix);


--
-- Name: team_memberships team_memberships_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_memberships
    ADD CONSTRAINT team_memberships_pkey PRIMARY KEY (id);


--
-- Name: team_memberships uq_one_team_per_affiliate; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_memberships
    ADD CONSTRAINT uq_one_team_per_affiliate UNIQUE (affiliate_id);


--
-- Name: webhook_failures webhook_failures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webhook_failures
    ADD CONSTRAINT webhook_failures_pkey PRIMARY KEY (id);


--
-- Name: ix_affiliates_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_affiliates_email ON public.affiliates USING btree (email);


--
-- Name: ix_affiliates_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_affiliates_id ON public.affiliates USING btree (id);


--
-- Name: ix_affiliates_referral_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_affiliates_referral_code ON public.affiliates USING btree (referral_code);


--
-- Name: ix_commissions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_commissions_id ON public.commissions USING btree (id);


--
-- Name: ix_payout_requests_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payout_requests_id ON public.payout_requests USING btree (id);


--
-- Name: ix_sales_teams_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sales_teams_id ON public.sales_teams USING btree (id);


--
-- Name: ix_team_memberships_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_team_memberships_id ON public.team_memberships USING btree (id);


--
-- Name: ix_webhook_failures_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_webhook_failures_id ON public.webhook_failures USING btree (id);


--
-- Name: ix_webhook_failures_subscription_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_webhook_failures_subscription_id ON public.webhook_failures USING btree (subscription_id);


--
-- Name: affiliates affiliates_referred_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.affiliates
    ADD CONSTRAINT affiliates_referred_by_id_fkey FOREIGN KEY (referred_by_id) REFERENCES public.affiliates(id);


--
-- Name: commissions commissions_earner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commissions
    ADD CONSTRAINT commissions_earner_id_fkey FOREIGN KEY (earner_id) REFERENCES public.affiliates(id);


--
-- Name: commissions commissions_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.commissions
    ADD CONSTRAINT commissions_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.affiliates(id);


--
-- Name: payout_requests payout_requests_affiliate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payout_requests
    ADD CONSTRAINT payout_requests_affiliate_id_fkey FOREIGN KEY (affiliate_id) REFERENCES public.affiliates(id);


--
-- Name: team_memberships team_memberships_affiliate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_memberships
    ADD CONSTRAINT team_memberships_affiliate_id_fkey FOREIGN KEY (affiliate_id) REFERENCES public.affiliates(id);


--
-- Name: team_memberships team_memberships_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_memberships
    ADD CONSTRAINT team_memberships_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.sales_teams(id);


--
-- PostgreSQL database dump complete
--

\unrestrict VxOdibSFgxrIa0Y0EePzzt9UmR92C2UQErJWhEBOoAPyDLnwGF0cWLeABZHO6wx

