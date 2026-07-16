-- Part 2 classification database schema.
--
-- It reproduces the Part 1 seeding schema and extends it with the columns
-- required by Part 2: the PROJECT_TYPE of every project, the ISIC Rev. 5
-- classification of every project and of every primary data file, and tags.

CREATE TABLE REPOSITORIES (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    url     TEXT NOT NULL
);

CREATE TABLE PROJECTS (
    id                          INTEGER PRIMARY KEY,
    query_string                TEXT,
    repository_id               INTEGER NOT NULL,
    repository_url              TEXT NOT NULL,
    project_url                 TEXT NOT NULL,
    version                     TEXT,
    title                       TEXT NOT NULL,
    description                 TEXT NOT NULL,
    language                    TEXT,
    doi                         TEXT,
    upload_date                 TEXT,
    download_date               TEXT NOT NULL,
    download_repository_folder  TEXT NOT NULL,
    download_project_folder     TEXT NOT NULL,
    download_version_folder     TEXT,
    download_method             TEXT NOT NULL,

    -- Part 2 Step 1: PROJECT_TYPE
    type                        TEXT NOT NULL DEFAULT 'NOT_A_PROJECT'
                                CHECK (type IN ('QDA_PROJECT', 'QD_PROJECT',
                                                'OTHER_PROJECT', 'NOT_A_PROJECT')),

    -- Part 2 Step 3: ISIC Rev. 5 classification of the project
    primary_class               TEXT,
    primary_class_name          TEXT,
    primary_section             TEXT,
    secondary_class             TEXT,
    secondary_class_name        TEXT,
    secondary_section           TEXT,
    classification_score        REAL,
    classification_confidence   TEXT,
    no_project_files            INTEGER NOT NULL DEFAULT 0,

    -- provenance, so a merged database stays traceable to its source
    source_db                   TEXT,
    source_project_id           INTEGER,

    FOREIGN KEY (repository_id) REFERENCES REPOSITORIES(id)
);

CREATE TABLE FILES (
    id                   INTEGER PRIMARY KEY,
    project_id           INTEGER NOT NULL,
    file_name            TEXT NOT NULL,
    file_type            TEXT NOT NULL,
    status               TEXT NOT NULL,

    -- Part 2: derived file taxonomy
    file_extension       TEXT,
    file_category        TEXT NOT NULL DEFAULT 'UNKNOWN'
                         CHECK (file_category IN ('QDA', 'PRIMARY', 'OTHER', 'UNKNOWN')),
    local_path           TEXT,
    text_chars           INTEGER NOT NULL DEFAULT 0,

    -- Part 2 Step 3: ISIC classification of each primary data file
    primary_class        TEXT,
    primary_class_name   TEXT,
    secondary_class      TEXT,
    secondary_class_name TEXT,
    classification_score REAL,

    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE KEYWORDS (
    id         INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    keyword    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE PERSON_ROLE (
    id         INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name       TEXT NOT NULL,
    role       TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

CREATE TABLE LICENSES (
    id         INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    license    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

-- Part 2 Step 2: "Also consider creating tags for searching"
CREATE TABLE TAGS (
    id         INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    tag        TEXT NOT NULL,
    weight     REAL,
    FOREIGN KEY (project_id) REFERENCES PROJECTS(id)
);

-- The ISIC Rev. 5 taxonomy the classification refers to, so the database is
-- self-describing and the full class names are available to any consumer.
CREATE TABLE ISIC_CLASSES (
    division     TEXT PRIMARY KEY,
    section      TEXT NOT NULL,
    section_name TEXT NOT NULL,
    name         TEXT NOT NULL
);

CREATE INDEX idx_files_project   ON FILES(project_id);
CREATE INDEX idx_files_category  ON FILES(file_category);
CREATE INDEX idx_projects_type   ON PROJECTS(type);
CREATE INDEX idx_projects_repo   ON PROJECTS(repository_id);
CREATE INDEX idx_tags_project    ON TAGS(project_id);
