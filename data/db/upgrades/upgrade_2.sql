-- version 1
--ALTER TABLE guilds ADD COLUMN StarboardChannel integer;
ALTER TABLE guilds RENAME COLUMN StarredChannel TO LogChannel;
