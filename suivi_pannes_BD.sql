-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 10, 2025 at 05:49 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `suivi_pannes_`
--

-- --------------------------------------------------------

--
-- Table structure for table `alerts`
--

CREATE TABLE `alerts` (
  `id` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  `site_name` varchar(255) NOT NULL,
  `url_or_ip` varchar(255) NOT NULL,
  `reason` text DEFAULT NULL,
  `is_acknowledged` varchar(25) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `alerts`
-
--
-- Table structure for table `architecture_sites`
--

CREATE TABLE `architecture_sites` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `architecture_id` int(11) DEFAULT NULL,
  `site_id` int(11) DEFAULT NULL,
  `position_x` int(11) DEFAULT NULL,
  `position_y` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `connections`
--

CREATE TABLE `connections` (
  `id` int(11) NOT NULL,
  `source_id` int(11) NOT NULL,
  `destination_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `created_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `connection_history`
--

CREATE TABLE `connection_history` (
  `id` int(11) NOT NULL,
  `connection_id` int(11) NOT NULL,
  `status` enum('active','degraded','down') NOT NULL,
  `checked_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `response_time` int(11) DEFAULT NULL COMMENT 'en ms',
  `packet_loss` decimal(5,2) DEFAULT NULL COMMENT 'en pourcentage'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `destination_email`
--

CREATE TABLE `destination_email` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `date_ajout` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `destination_email`
---------------------------------------------

--
-- Table structure for table `monitored_sites`
--

CREATE TABLE `monitored_sites` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `url_or_ip` varchar(255) NOT NULL,
  `enabled` tinyint(1) DEFAULT 1,
  `last_status` varchar(50) DEFAULT NULL,
  `last_checked` datetime DEFAULT NULL,
  `failed_pings_count` int(11) DEFAULT 0,
  `alert_sent` tinyint(1) DEFAULT 0,
  `equipment_type` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `monitored_sites`
-----------------------------------------------

--
-- Table structure for table `monitoring_events`
--

CREATE TABLE `monitoring_events` (
  `id` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  `timestamp` datetime NOT NULL,
  `status` varchar(50) NOT NULL,
  `reason` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `monitoring_events`
--------------------

--
-- Table structure for table `network_architectures`
--

CREATE TABLE `network_architectures` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `created_by` varchar(100) DEFAULT 'admin',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `network_architectures`
--

-- --------------------------------------------------------

--
-- Table structure for table `network_connections`
--

CREATE TABLE `network_connections` (
  `id` int(11) NOT NULL,
  `source_device_id` int(11) NOT NULL,
  `target_device_id` int(11) NOT NULL,
  `connection_type` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `network_devices`
--

CREATE TABLE `network_devices` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `ip_address` varchar(255) DEFAULT NULL,
  `device_type` enum('serveur','switch','routeur','firewall','autre') NOT NULL,
  `position_x` int(11) DEFAULT NULL,
  `position_y` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `site_connections`
--

CREATE TABLE `site_connections` (
  `id` int(11) NOT NULL,
  `architecture_id` int(11) NOT NULL,
  `source_site_id` int(11) NOT NULL,
  `target_site_id` int(11) NOT NULL,
  `connection_type` enum('standard','backup','ha','physical','logical') DEFAULT 'standard',
  `bandwidth` varchar(50) DEFAULT NULL,
  `latency` int(11) DEFAULT NULL COMMENT 'en ms',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `site_connections`
--

-----------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `prenom` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `poste` varchar(255) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `photo_profile` varchar(255) DEFAULT NULL,
  `password` varchar(100) NOT NULL,
  `role` varchar(20) DEFAULT 'admin'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--


--
-- Indexes for dumped tables
--

--
-- Indexes for table `alerts`
--
ALTER TABLE `alerts`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `architecture_sites`
--
ALTER TABLE `architecture_sites`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `connections`
--
ALTER TABLE `connections`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `source_id` (`source_id`,`destination_id`),
  ADD KEY `destination_id` (`destination_id`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `connection_history`
--
ALTER TABLE `connection_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_connection_status` (`connection_id`,`status`),
  ADD KEY `idx_checked_at` (`checked_at`);

--
-- Indexes for table `destination_email`
--
ALTER TABLE `destination_email`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `monitored_sites`
--
ALTER TABLE `monitored_sites`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `monitoring_events`
--
ALTER TABLE `monitoring_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `site_id` (`site_id`);

--
-- Indexes for table `network_architectures`
--
ALTER TABLE `network_architectures`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_arch_name` (`name`);

--
-- Indexes for table `network_connections`
--
ALTER TABLE `network_connections`
  ADD PRIMARY KEY (`id`),
  ADD KEY `source_device_id` (`source_device_id`),
  ADD KEY `target_device_id` (`target_device_id`);

--
-- Indexes for table `network_devices`
--
ALTER TABLE `network_devices`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `site_connections`
--
ALTER TABLE `site_connections`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `no_duplicate_connections` (`architecture_id`,`source_site_id`,`target_site_id`),
  ADD KEY `target_site_id` (`target_site_id`),
  ADD KEY `idx_arch_connections` (`architecture_id`),
  ADD KEY `idx_site_connections` (`source_site_id`,`target_site_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `alerts`
--
ALTER TABLE `alerts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1085;

--
-- AUTO_INCREMENT for table `architecture_sites`
--
ALTER TABLE `architecture_sites`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `connections`
--
ALTER TABLE `connections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `connection_history`
--
ALTER TABLE `connection_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `destination_email`
--
ALTER TABLE `destination_email`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `monitored_sites`
--
ALTER TABLE `monitored_sites`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT for table `monitoring_events`
--
ALTER TABLE `monitoring_events`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4097;

--
-- AUTO_INCREMENT for table `network_architectures`
--
ALTER TABLE `network_architectures`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `network_connections`
--
ALTER TABLE `network_connections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `network_devices`
--
ALTER TABLE `network_devices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `site_connections`
--
ALTER TABLE `site_connections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `connections`
--
ALTER TABLE `connections`
  ADD CONSTRAINT `connections_ibfk_1` FOREIGN KEY (`source_id`) REFERENCES `monitored_sites` (`id`),
  ADD CONSTRAINT `connections_ibfk_2` FOREIGN KEY (`destination_id`) REFERENCES `monitored_sites` (`id`),
  ADD CONSTRAINT `connections_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

--
-- Constraints for table `connection_history`
--
ALTER TABLE `connection_history`
  ADD CONSTRAINT `connection_history_ibfk_1` FOREIGN KEY (`connection_id`) REFERENCES `site_connections` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `monitoring_events`
--
ALTER TABLE `monitoring_events`
  ADD CONSTRAINT `monitoring_events_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `monitored_sites` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `network_connections`
--
ALTER TABLE `network_connections`
  ADD CONSTRAINT `network_connections_ibfk_1` FOREIGN KEY (`source_device_id`) REFERENCES `network_devices` (`id`),
  ADD CONSTRAINT `network_connections_ibfk_2` FOREIGN KEY (`target_device_id`) REFERENCES `network_devices` (`id`);

--
-- Constraints for table `site_connections`
--
ALTER TABLE `site_connections`
  ADD CONSTRAINT `site_connections_ibfk_1` FOREIGN KEY (`architecture_id`) REFERENCES `network_architectures` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `site_connections_ibfk_2` FOREIGN KEY (`source_site_id`) REFERENCES `monitored_sites` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `site_connections_ibfk_3` FOREIGN KEY (`target_site_id`) REFERENCES `monitored_sites` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
