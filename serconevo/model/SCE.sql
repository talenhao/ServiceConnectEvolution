-- MySQL dump 10.13  Distrib 5.1.73, for redhat-linux-gnu (x86_64)
--
-- Host: 192.168.1.138    Database: yed_collect
-- ------------------------------------------------------
-- Server version	5.6.27-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `service_connections_table`
--

DROP TABLE IF EXISTS `service_connections_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `service_connections_table` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'primary key',
  `c_ip` varchar(255) NOT NULL COMMENT 'connection ip',
  `c_port` varchar(255) NOT NULL COMMENT 'connection port',
  `p_name` varchar(255) NOT NULL COMMENT 'process name',
  `p_pid` varchar(5) NOT NULL COMMENT 'process name',
  `p_exe` varchar(255) NOT NULL COMMENT 'process exe',
  `p_cwd` varchar(255) NOT NULL COMMENT 'process cwd',
  `p_status` varchar(10) NOT NULL COMMENT 'process status',
  `p_create_time` datetime NOT NULL COMMENT 'process create time',
  `p_username` varchar(20) NOT NULL COMMENT 'process username',
  `server_uuid` char(36) NOT NULL COMMENT 'server machine id',
  `CreateTime` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'record create time',
  `p_cmdline` text NOT NULL COMMENT 'process cmdline',
  PRIMARY KEY (`id`),
  UNIQUE KEY `pid_ip_port` (`p_pid`,`c_ip`,`c_port`),
  KEY `server_uuid_index` (`server_uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=143 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `service_listens_table`
--

DROP TABLE IF EXISTS `service_listens_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `service_listens_table` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'primary key',
  `l_ip` varchar(255) NOT NULL COMMENT 'listening ip',
  `l_port` varchar(255) NOT NULL COMMENT 'listening port',
  `p_name` varchar(40) NOT NULL COMMENT 'process name',
  `p_pid` varchar(5) NOT NULL COMMENT 'process name',
  `p_exe` varchar(255) NOT NULL COMMENT 'process exe',
  `p_cwd` varchar(255) NOT NULL COMMENT 'process cwd',
  `p_status` varchar(10) NOT NULL COMMENT 'process status',
  `p_create_time` datetime NOT NULL COMMENT 'process create time',
  `p_username` varchar(20) NOT NULL COMMENT 'process username',
  `server_uuid` char(36) NOT NULL COMMENT 'server machine id',
  `CreateTime` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'record create time',
  `p_cmdline` text NOT NULL COMMENT 'process cmdline',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_port` (`l_ip`,`l_port`),
  KEY `server_uuid_index` (`server_uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-09-08  0:58:31
