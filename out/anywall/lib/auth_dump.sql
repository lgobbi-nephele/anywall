-- MySQL dump 10.13  Distrib 8.4.3, for Win64 (x86_64)
--
-- Host: localhost    Database: mydatabase
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$LFQikuGOg96atKB2CIEPQt$xUTO83jt4XR3lN3S28R8GXIGrNuo4ZV/qRKLwpV+QfA=','2025-03-10 11:17:43.138461',1,'admin','','','l.gobbi@nephelesrl.it',1,1,'2025-03-09 18:29:05.205021');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add window',7,'add_window'),(26,'Can change window',7,'change_window'),(27,'Can delete window',7,'delete_window'),(28,'Can view window',7,'view_window'),(29,'Can add requested window',8,'add_requestedwindow'),(30,'Can change requested window',8,'change_requestedwindow'),(31,'Can delete requested window',8,'delete_requestedwindow'),(32,'Can view requested window',8,'view_requestedwindow'),(33,'Can add backup window',9,'add_backupwindow'),(34,'Can change backup window',9,'change_backupwindow'),(35,'Can delete backup window',9,'delete_backupwindow'),(36,'Can view backup window',9,'view_backupwindow'),(37,'Can add image model',10,'add_imagemodel'),(38,'Can change image model',10,'change_imagemodel'),(39,'Can delete image model',10,'delete_imagemodel'),(40,'Can view image model',10,'view_imagemodel'),(41,'Can add state',11,'add_state'),(42,'Can change state',11,'change_state'),(43,'Can delete state',11,'delete_state'),(44,'Can view state',11,'view_state'),(45,'Can add api_calls',12,'add_api_calls'),(46,'Can change api_calls',12,'change_api_calls'),(47,'Can delete api_calls',12,'delete_api_calls'),(48,'Can view api_calls',12,'view_api_calls'),(49,'Can add delta',13,'add_delta'),(50,'Can change delta',13,'change_delta'),(51,'Can delete delta',13,'delete_delta'),(52,'Can view delta',13,'view_delta'),(53,'Can add signaling message',14,'add_signalingmessage'),(54,'Can change signaling message',14,'change_signalingmessage'),(55,'Can delete signaling message',14,'delete_signalingmessage'),(56,'Can view signaling message',14,'view_signalingmessage');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(12,'anywall_app','api_calls'),(9,'anywall_app','backupwindow'),(13,'anywall_app','delta'),(10,'anywall_app','imagemodel'),(8,'anywall_app','requestedwindow'),(14,'anywall_app','signalingmessage'),(11,'anywall_app','state'),(7,'anywall_app','window'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('b0bkxuibxzbjgerqkd26cu4ks6tigj51','.eJxVjEEOwiAQRe_C2hDGCtO6dO8ZyAwMUjWQlHZlvLuSdKHb997_L-VpW7Pfmix-juqsQB1-GVN4SOki3qncqg61rMvMuid6t01fa5TnZW__DjK13NdAJ-MQjhiQBR0YSAxIQwyTS8kZDvgFgawIMo4pWktkDYwDA-Ok3h_skThW:1trb4c:GdTzIT85nt1DYhEjjN2AyTijjJ9I-x-iuz1w-4_gAqY','2025-03-24 11:13:30.027599'),('gac8f36xrfnhbitidabsxo8p6dn1q5cq','.eJxVjLEOAiEQRP-F2hDxAMHS3m8gu-wipwaS464y_ruQXKHFZJJ5M_MWAbY1h63xEmYSF6HE4TdDiE8uA9ADyr3KWMu6zChHRe60yVslfl337t9Bhpb7-pQQpqjBeGZ0hm13MDZOXjliSuqY0A65pF0iZYjoHC3qHmlPSXy-Hew5nQ:1trb8h:kI79ABEhcMXpzjj3arpyEnurmcf1iLZnAnqQleo52TQ','2025-03-24 11:17:43.151066'),('ls5x2iuz0tulzl9b1z85bgv9it4pi76z','.eJxVjEEOwiAQRe_C2hDGCtO6dO8ZyAwMUjWQlHZlvLuSdKHb997_L-VpW7Pfmix-juqsQB1-GVN4SOki3qncqg61rMvMuid6t01fa5TnZW__DjK13NdAJ-MQjhiQBR0YSAxIQwyTS8kZDvgFgawIMo4pWktkDYwDA-Ok3h_skThW:1trLOp:CDo5OYApJnpZ6VzUMhWsy7nmmC-drlYtefuogFJSpX0','2025-03-23 18:29:19.195759'),('q14cf6036duwoghgk7sfr54nseg29k69','.eJxVjEEOwiAQRe_C2hDGCtO6dO8ZyAwMUjWQlHZlvLuSdKHb997_L-VpW7Pfmix-juqsQB1-GVN4SOki3qncqg61rMvMuid6t01fa5TnZW__DjK13NdAJ-MQjhiQBR0YSAxIQwyTS8kZDvgFgawIMo4pWktkDYwDA-Ok3h_skThW:1trLPG:m9-4uIr30Gq8oGIqfTVUDUoV43LY2_Y13ULzzg491Ew','2025-03-23 18:29:46.996282'),('r6s970s5mqbd3y5cl3cwoqzdycnel06y','.eJxVjEEOwiAQRe_C2hDGCtO6dO8ZyAwMUjWQlHZlvLuSdKHb997_L-VpW7Pfmix-juqsQB1-GVN4SOki3qncqg61rMvMuid6t01fa5TnZW__DjK13NdAJ-MQjhiQBR0YSAxIQwyTS8kZDvgFgawIMo4pWktkDYwDA-Ok3h_skThW:1trb74:3GV7ZiwJjlWoIdWoaAveSlXHoRTneEWP-AsLtuIl7WM','2025-03-24 11:16:02.550131');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-03-10 12:18:22
