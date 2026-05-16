create table if not exists teachers (
    id integer primary key,
    name text not null,
    email text,
    created_at text not null default current_timestamp,
    unique (email)
);

create table if not exists teacher_pins (
    id integer primary key,
    teacher_id integer not null references teachers(id) on delete cascade,
    school_year text not null,
    pin_code text not null check (pin_code glob '[0-9][0-9][0-9][0-9]'),
    pin_hash text not null,
    created_at text not null default current_timestamp,
    unique (teacher_id, school_year)
);

create table if not exists evaluations (
    id integer primary key,
    teacher_id integer not null references teachers(id) on delete restrict,
    title text not null,
    school_year text not null,
    grade integer not null check (grade between 1 and 10),
    class_group text not null,
    subject text not null,
    questionnaire_version text not null,
    expected_participants integer not null check (expected_participants >= 0),
    base_url text not null default '',
    status text not null default 'prepared' check (
        status in (
            'prepared',
            'active',
            'joining',
            'reading',
            'answering',
            'paused',
            'review_required',
            'closed',
            'deactivated'
        )
    ),
    current_item_index integer,
    previous_status text check (
        previous_status is null or previous_status in (
            'prepared',
            'active',
            'joining',
            'reading',
            'answering',
            'review_required'
        )
    ),
    student_token text not null,
    teacher_token text not null,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    unique (student_token),
    unique (teacher_token),
    unique (school_year, class_group, subject, teacher_id)
);

create table if not exists participants (
    id integer primary key,
    evaluation_id integer not null references evaluations(id) on delete cascade,
    animal_code text not null,
    joined_at text not null default current_timestamp,
    last_seen_at text,
    unique (id, evaluation_id),
    unique (evaluation_id, animal_code)
);

create table if not exists live_answers (
    id integer primary key,
    evaluation_id integer not null references evaluations(id) on delete cascade,
    participant_id integer not null,
    item_key text not null,
    answer_value integer not null check (answer_value between 0 and 3),
    answered_at text not null default current_timestamp,
    foreign key (participant_id, evaluation_id)
        references participants(id, evaluation_id) on delete cascade,
    unique (participant_id, item_key)
);

create table if not exists item_aggregates (
    id integer primary key,
    evaluation_id integer not null references evaluations(id) on delete cascade,
    item_key text not null,
    count_0 integer not null default 0 check (count_0 >= 0),
    count_1 integer not null default 0 check (count_1 >= 0),
    count_2 integer not null default 0 check (count_2 >= 0),
    count_3 integer not null default 0 check (count_3 >= 0),
    missing_count integer not null default 0 check (missing_count >= 0),
    joined_count integer not null default 0 check (joined_count >= 0),
    mean real check (mean is null or mean between 0 and 3),
    unique (evaluation_id, item_key)
);

create table if not exists admin_log (
    id integer primary key,
    actor text not null,
    action text not null,
    evaluation_id integer references evaluations(id) on delete set null,
    target_evaluation_id integer,
    details text,
    created_at text not null default current_timestamp
);
