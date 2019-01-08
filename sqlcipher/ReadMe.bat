sqlcipher EnMicroMsg.db
<<<<<<< HEAD
PRAGMA key = "74ee691";PRAGMA cipher_use_hmac = off;PRAGMA kdf_iter = 4000;ATTACH DATABASE "decrypted.db" AS decrypted_db KEY "";SELECT sqlcipher_export("decrypted_db");DETACH DATABASE decrypted_db;
=======
<<<<<<< HEAD
PRAGMA key = "74ee691";PRAGMA cipher_use_hmac = off;PRAGMA kdf_iter = 4000;ATTACH DATABASE "New.db" AS new_db KEY "";SELECT sqlcipher_export("new_db");DETACH DATABASE new_db;
=======
<<<<<<< HEAD
PRAGMA key = "74ee691";
PRAGMA cipher_use_hmac = off;
PRAGMA kdf_iter = 4000;
ATTACH DATABASE "decrypted_database.db" AS decrypted_database KEY "";
SELECT sqlcipher_export("decrypted_database");
DETACH DATABASE decrypted_database;
=======
PRAGMA key = "74ee691";PRAGMA cipher_use_hmac = off;PRAGMA kdf_iter = 4000;ATTACH DATABASE "New.db" AS new_db KEY "";SELECT sqlcipher_export("new_db");DETACH DATABASE new_db;
>>>>>>> 682bd59... Modified scripts, add SqlCipher, userdict, stopwords, font.
>>>>>>> e62f48a... Add gitignore, getPsw function, add SqlCipher, userdict, stopwords, font
>>>>>>> 3d4e34d... Modified scripts, add SqlCipher, userdict, stopwords, font.
