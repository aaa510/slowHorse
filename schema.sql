drop table if exists point_transactions;
drop table if exists answers;
drop table if exists question_options;
drop table if exists questions;
drop table if exists notification_outbox;
drop table if exists discussion_replies;
drop table if exists discussion_posts;
drop table if exists users;

create table users (
    id integer primary key autoincrement,
    username text unique not null,
    fan_driver text,
    password_hash text not null,
    points integer not null default 1000,
    login_days integer not null default 0,
    last_login_award_date text,
    created_at text not null default current_timestamp
);

create table questions (
    id integer primary key autoincrement,
    creator_id integer not null,
    race_round integer not null,
    race_name text not null,
    race_start_at text not null,
    title text not null,
    stake integer not null,
    status text not null default 'open',
    correct_option_id integer,
    settled_at text,
    created_at text not null default current_timestamp,
    foreign key (creator_id) references users (id),
    foreign key (correct_option_id) references question_options (id)
);

create table question_options (
    id integer primary key autoincrement,
    question_id integer not null,
    label text not null,
    position integer not null,
    foreign key (question_id) references questions (id)
);

create table answers (
    id integer primary key autoincrement,
    question_id integer not null,
    user_id integer not null,
    option_id integer not null,
    bet integer not null default 0,
    is_correct integer,
    points_awarded integer not null default 0,
    created_at text not null default current_timestamp,
    foreign key (question_id) references questions (id),
    foreign key (user_id) references users (id),
    foreign key (option_id) references question_options (id),
    unique (question_id, user_id)
);

create table point_transactions (
    id integer primary key autoincrement,
    user_id integer not null,
    question_id integer,
    amount integer not null,
    reason text not null,
    created_at text not null default current_timestamp,
    foreign key (user_id) references users (id),
    foreign key (question_id) references questions (id)
);

create table discussion_posts (
    id integer primary key autoincrement,
    user_id integer not null,
    title text not null,
    body text not null,
    created_at text not null default current_timestamp,
    foreign key (user_id) references users (id)
);

create table discussion_replies (
    id integer primary key autoincrement,
    post_id integer not null,
    user_id integer not null,
    body text,
    image_path text,
    created_at text not null default current_timestamp,
    foreign key (post_id) references discussion_posts (id),
    foreign key (user_id) references users (id)
);

create table notification_outbox (
    id integer primary key autoincrement,
    message text not null,
    status text not null default 'pending',
    attempts integer not null default 0,
    last_error text,
    created_at text not null default current_timestamp,
    sent_at text
);
