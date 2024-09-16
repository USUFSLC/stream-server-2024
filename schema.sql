CREATE TABLE streams
( key TEXT PRIMARY KEY
, created INT NOT NULL
, started INT
, duration INT
, name TEXT NOT NULL
, presenter TEXT NOT NULL
, description TEXT NOT NULL
);

CREATE TABLE current_stream ( key TEXT NOT NULL UNIQUE );
