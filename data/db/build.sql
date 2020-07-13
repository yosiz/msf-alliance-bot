--version 2
create TABLE IF NOT EXISTS guilds (
    GuildID integer PRIMARY KEY,
    WelcomeChannel integer DEFAULT NULL,
    StarboardChannel integer DEFAULT NULL,
    DefaultMemberRoles text,
    Prefix text DEFAULT "+"
);

create TABLE IF NOT EXISTS exp (
    UserID integer PRIMARY KEY,
    GuildID integer,
    XP integer DEFAULT 0 ,
    Level integer DEFAULT 0,
    XPLock text DEFAULT CURRENT_TIMESTAMP
);

create TABLE IF NOT EXISTS mutes (
    UserID integer PRIMARY KEY,
    RoleIDs text,
    EndTime text
);

create TABLE IF NOT EXISTS reaction_roles (
    GuildID integer NOT NULL,
    ReactionID text NOT NULL,
    RoleID text NOT NULL,
    PRIMARY KEY(GuildID,ReactionId)
);

create TABLE IF NOT EXISTS starboard (
    RootMessageID integer PRIMARY KEY,
    StarMessageID ineteger,
    Stars integer DEFAULT 1

);