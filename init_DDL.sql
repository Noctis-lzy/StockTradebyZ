-- 股票交易系统数据库初始化脚本
-- 版本：1.0
-- 日期：2024-01-01

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `zx_4lu_stock` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `zx_4lu_stock`;

-- 设置时区
SET time_zone = '+08:00';

-- 创建任务基础表
CREATE TABLE `tasks` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '任务 ID（主键）',
  `task_id` VARCHAR(36) NOT NULL COMMENT '任务唯一标识（UUID）',
  `task_name` VARCHAR(255) NOT NULL COMMENT '任务名称',
  `task_description` TEXT COMMENT '任务描述',
  `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型：stock_selection-选股任务，batch_backtest-批量回测任务，single_backtest-个股回测任务',
  `status` VARCHAR(50) DEFAULT 'pending' COMMENT '任务状态：pending-待执行，running-执行中，completed-已完成，failed-失败，cancelled-已取消',
  `priority` BIGINT UNSIGNED DEFAULT 5 COMMENT '任务优先级（1-10）',
  `created_by` VARCHAR(36) COMMENT '创建用户 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` VARCHAR(36) COMMENT '最后修改用户 ID',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
  `last_run_time` DATETIME COMMENT '最后执行时间',
  `timeout` BIGINT UNSIGNED DEFAULT 3600 COMMENT '超时时间（秒）',
  `retry_count` BIGINT UNSIGNED DEFAULT 3 COMMENT '重试次数',
  `is_enabled` BIGINT UNSIGNED DEFAULT 1 COMMENT '是否启用：0-禁用，1-启用',
  `tags` TEXT COMMENT '标签（JSON 数组字符串）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_task_type` (`task_type`),
  KEY `idx_status` (`status`),
  KEY `idx_next_run_time` (`next_run_time`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_task_name` (`task_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务基础表';

-- 创建任务配置表
CREATE TABLE `task_configs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '配置 ID（主键）',
  `task_id` VARCHAR(36) NOT NULL COMMENT '任务 ID（外键）',
  `config_key` VARCHAR(100) NOT NULL COMMENT '配置键',
  `config_value` TEXT NOT NULL COMMENT '配置值（JSON 格式字符串）',
  `config_type` VARCHAR(50) NOT NULL COMMENT '配置类型',
  `version` BIGINT UNSIGNED DEFAULT 1 COMMENT '配置版本',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_config_key` (`config_key`),
  KEY `idx_config_type` (`config_type`),
  KEY `idx_version` (`version`),
  CONSTRAINT `fk_task_configs_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE COMMENT '关联 tasks 表的 task_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务配置表';

-- 创建任务执行记录表
CREATE TABLE `task_executions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '执行记录 ID（主键）',
  `execution_id` VARCHAR(36) NOT NULL COMMENT '执行唯一标识（UUID）',
  `task_id` VARCHAR(36) NOT NULL COMMENT '任务 ID（外键）',
  `status` VARCHAR(50) DEFAULT 'pending' COMMENT '执行状态：pending-待执行，running-执行中，completed-已完成，failed-失败，cancelled-已取消',
  `progress` BIGINT UNSIGNED DEFAULT 0 COMMENT '执行进度（0-100）',
  `current_stage` VARCHAR(100) COMMENT '当前执行阶段',
  `started_at` DATETIME COMMENT '开始执行时间',
  `finished_at` DATETIME COMMENT '完成时间',
  `duration` BIGINT UNSIGNED COMMENT '执行耗时（秒）',
  `error_message` TEXT COMMENT '错误信息',
  `result_file_path` VARCHAR(500) COMMENT '结果文件路径',
  `result_size` BIGINT UNSIGNED COMMENT '结果数据大小（字节）',
  `created_by` VARCHAR(36) COMMENT '触发用户 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_execution_id` (`execution_id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_status` (`status`),
  KEY `idx_started_at` (`started_at`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_task_executions_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE COMMENT '关联 tasks 表的 task_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行记录表';

-- 创建任务执行日志表
CREATE TABLE `task_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志 ID（主键）',
  `execution_id` VARCHAR(36) NOT NULL COMMENT '执行记录 ID（外键）',
  `log_level` VARCHAR(50) DEFAULT 'INFO' COMMENT '日志级别：DEBUG-调试信息，INFO-一般信息，WARNING-警告信息，ERROR-错误信息',
  `log_message` TEXT NOT NULL COMMENT '日志消息',
  `log_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日志时间',
  `log_source` VARCHAR(100) COMMENT '日志来源',
  `extra_data` TEXT COMMENT '额外数据（JSON 格式字符串）',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_log_level` (`log_level`),
  KEY `idx_log_time` (`log_time`),
  CONSTRAINT `fk_task_logs_execution_id` FOREIGN KEY (`execution_id`) REFERENCES `task_executions` (`execution_id`) ON DELETE CASCADE COMMENT '关联 task_executions 表的 execution_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行日志表';
-- PARTITION BY RANGE (TO_DAYS(log_time)) (
--   PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
--   PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
--   PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01')),
--   PARTITION p202404 VALUES LESS THAN (TO_DAYS('2024-05-01')),
--   PARTITION p202405 VALUES LESS THAN (TO_DAYS('2024-06-01')),
--   PARTITION p202406 VALUES LESS THAN (TO_DAYS('2024-07-01')),
--   PARTITION p202407 VALUES LESS THAN (TO_DAYS('2024-08-01')),
--   PARTITION p202408 VALUES LESS THAN (TO_DAYS('2024-09-01')),
--   PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
--   PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
--   PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
--   PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
--   PARTITION pmax VALUES LESS THAN MAXVALUE
-- );

-- 创建选股任务结果表
CREATE TABLE `stock_selection_results` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '结果 ID（主键）',
  `execution_id` VARCHAR(36) NOT NULL COMMENT '执行记录 ID（外键）',
  `stock_code` VARCHAR(10) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(100) COMMENT '股票名称',
  `match_score` DECIMAL(10,4) COMMENT '匹配度（0-100）',
  `match_reasons` TEXT COMMENT '匹配原因（JSON 数组字符串）',
  `selection_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选股时间',
  `extra_data` TEXT COMMENT '额外数据（JSON 格式字符串）',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_stock_code` (`stock_code`),
  KEY `idx_match_score` (`match_score`),
  KEY `idx_selection_time` (`selection_time`),
  CONSTRAINT `fk_stock_selection_results_execution_id` FOREIGN KEY (`execution_id`) REFERENCES `task_executions` (`execution_id`) ON DELETE CASCADE COMMENT '关联 task_executions 表的 execution_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选股任务结果表';

-- 创建批量回测任务结果表
CREATE TABLE `backtest_results` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '结果 ID（主键）',
  `execution_id` VARCHAR(36) NOT NULL COMMENT '执行记录 ID（外键）',
  `stock_code` VARCHAR(10) NOT NULL COMMENT '股票代码',
  `stock_name` VARCHAR(100) COMMENT '股票名称',
  `total_return` DECIMAL(10,4) COMMENT '总收益率',
  `annual_return` DECIMAL(10,4) COMMENT '年化收益率',
  `sharpe_ratio` DECIMAL(10,4) COMMENT '夏普比率',
  `max_drawdown` DECIMAL(10,4) COMMENT '最大回撤',
  `win_rate` DECIMAL(10,4) COMMENT '胜率',
  `profit_loss_ratio` DECIMAL(10,4) COMMENT '盈亏比',
  `total_trades` BIGINT UNSIGNED COMMENT '总交易次数',
  `winning_trades` BIGINT UNSIGNED COMMENT '盈利交易次数',
  `losing_trades` BIGINT UNSIGNED COMMENT '亏损交易次数',
  `backtest_start_date` DATETIME COMMENT '回测开始日期',
  `backtest_end_date` DATETIME COMMENT '回测结束日期',
  `extra_data` TEXT COMMENT '额外数据（JSON 格式字符串）',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_stock_code` (`stock_code`),
  KEY `idx_total_return` (`total_return`),
  KEY `idx_win_rate` (`win_rate`),
  CONSTRAINT `fk_backtest_results_execution_id` FOREIGN KEY (`execution_id`) REFERENCES `task_executions` (`execution_id`) ON DELETE CASCADE COMMENT '关联 task_executions 表的 execution_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='批量回测任务结果表';

-- 创建交易明细表
CREATE TABLE `trade_details` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '交易 ID（主键）',
  `result_id` BIGINT UNSIGNED NOT NULL COMMENT '回测结果 ID（外键）',
  `stock_code` VARCHAR(10) NOT NULL COMMENT '股票代码',
  `trade_type` VARCHAR(50) NOT NULL COMMENT '交易类型：buy-买入，sell-卖出',
  `trade_date` DATETIME NOT NULL COMMENT '交易日期',
  `trade_price` DECIMAL(10,2) NOT NULL COMMENT '交易价格',
  `trade_quantity` BIGINT UNSIGNED NOT NULL COMMENT '交易数量',
  `trade_amount` DECIMAL(15,2) NOT NULL COMMENT '交易金额',
  `profit_loss` DECIMAL(15,2) COMMENT '盈亏金额',
  `profit_loss_rate` DECIMAL(10,4) COMMENT '盈亏比例',
  `trade_reason` VARCHAR(500) COMMENT '交易原因',
  `extra_data` TEXT COMMENT '额外数据（JSON 格式字符串）',
  PRIMARY KEY (`id`),
  KEY `idx_result_id` (`result_id`),
  KEY `idx_stock_code` (`stock_code`),
  KEY `idx_trade_date` (`trade_date`),
  KEY `idx_trade_type` (`trade_type`),
  CONSTRAINT `fk_trade_details_result_id` FOREIGN KEY (`result_id`) REFERENCES `backtest_results` (`id`) ON DELETE CASCADE COMMENT '关联 backtest_results 表的 id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';
-- PARTITION BY RANGE (TO_DAYS(trade_date)) (
--   PARTITION p2020 VALUES LESS THAN (TO_DAYS('2021-01-01')),
--   PARTITION p2021 VALUES LESS THAN (TO_DAYS('2022-01-01')),
--   PARTITION p2022 VALUES LESS THAN (TO_DAYS('2023-01-01')),
--   PARTITION p2023 VALUES LESS THAN (TO_DAYS('2024-01-01')),
--   PARTITION p2024 VALUES LESS THAN (TO_DAYS('2025-01-01')),
--   PARTITION p2025 VALUES LESS THAN (TO_DAYS('2026-01-01')),
--   PARTITION p2026 VALUES LESS THAN (TO_DAYS('2027-01-01')),
--   PARTITION p2027 VALUES LESS THAN (TO_DAYS('2028-01-01')),
--   PARTITION p2028 VALUES LESS THAN (TO_DAYS('2029-01-01')),
--   PARTITION pmax VALUES LESS THAN MAXVALUE
-- );

-- 创建任务依赖表
CREATE TABLE `task_dependencies` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '依赖 ID（主键）',
  `task_id` VARCHAR(36) NOT NULL COMMENT '任务 ID（外键）',
  `depends_on_task_id` VARCHAR(36) NOT NULL COMMENT '依赖的任务 ID（外键）',
  `dependency_type` VARCHAR(50) NOT NULL COMMENT '依赖类型：predecessor-前置任务，successor-后置任务',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_dependency` (`task_id`, `depends_on_task_id`, `dependency_type`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_depends_on_task_id` (`depends_on_task_id`),
  CONSTRAINT `fk_task_dependencies_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE COMMENT '关联 tasks 表的 task_id 字段',
  CONSTRAINT `fk_task_dependencies_depends_on_task_id` FOREIGN KEY (`depends_on_task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE COMMENT '关联 tasks 表的 task_id 字段'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务依赖表';

-- 创建任务模板表
CREATE TABLE `task_templates` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '模板 ID（主键）',
  `template_id` VARCHAR(36) NOT NULL COMMENT '模板唯一标识（UUID）',
  `template_name` VARCHAR(255) NOT NULL COMMENT '模板名称',
  `template_description` TEXT COMMENT '模板描述',
  `template_type` VARCHAR(50) NOT NULL COMMENT '模板类型：stock_selection-选股模板，batch_backtest-批量回测模板，single_backtest-个股回测模板',
  `template_config` TEXT NOT NULL COMMENT '模板配置（JSON 格式字符串）',
  `is_public` BIGINT UNSIGNED DEFAULT 0 COMMENT '是否公开：0-私有，1-公开',
  `created_by` VARCHAR(36) COMMENT '创建用户 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_id` (`template_id`),
  KEY `idx_template_type` (`template_type`),
  KEY `idx_is_public` (`is_public`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_template_name` (`template_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务模板表';



-- 创建指标表
CREATE TABLE `indicators` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '指标 ID（主键）',
  `indicator_id` VARCHAR(36) NOT NULL COMMENT '指标唯一标识（UUID）',
  `indicator_code` VARCHAR(100) NOT NULL COMMENT '指标代码：唯一标识，用于系统调用',
  `indicator_name` VARCHAR(255) NOT NULL COMMENT '指标名称',
  `indicator_description` TEXT COMMENT '指标描述',
  `calculation_formula` TEXT COMMENT '计算公式：指标的计算方法',
  `default_params` TEXT COMMENT '默认参数：JSON 格式字符串',
  `indicator_type` VARCHAR(50) NOT NULL COMMENT '指标类型：price-价格指标，trend-趋势指标，momentum-动量指标，volume-成交量指标',
  `is_system` BIGINT UNSIGNED DEFAULT 1 COMMENT '是否系统指标：0-非系统指标，1-系统指标',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_indicator_id` (`indicator_id`),
  UNIQUE KEY `uk_indicator_code` (`indicator_code`),
  KEY `idx_indicator_type` (`indicator_type`),
  KEY `idx_is_system` (`is_system`),
  KEY `idx_indicator_name` (`indicator_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='指标表';

-- 创建指标参数表
CREATE TABLE `indicators_params` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '参数 ID（主键）',
  `indicator_id` VARCHAR(36) NOT NULL COMMENT '策略 ID（外键）',
  `param_key` VARCHAR(100) NOT NULL COMMENT '参数键：参数名称',
  `param_value` TEXT COMMENT '参数值：参数值，支持不同类型',
  `param_type` VARCHAR(50) NOT NULL COMMENT '参数类型：string-字符串，number-数字，boolean-布尔值',
  `description` VARCHAR(500) COMMENT '参数描述：参数的说明和用途',
  `is_required` BIGINT UNSIGNED DEFAULT 0 COMMENT '是否必填：0-可选，1-必填',
  `default_value` TEXT COMMENT '默认值：参数的默认值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_indicator_id` (`indicator_id`),
  KEY `idx_param_key` (`param_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略参数表';

-- 创建策略表
CREATE TABLE `strategies` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '策略 ID（主键）',
  `strategy_id` VARCHAR(36) NOT NULL COMMENT '策略唯一标识（UUID）',
  `strategy_name` VARCHAR(255) NOT NULL COMMENT '策略名称',
  `strategy_description` TEXT COMMENT '策略描述',
  `strategy_type` VARCHAR(50) NOT NULL COMMENT '策略类型：system-系统默认策略，custom-用户自定义策略',
  `py_class_path` VARCHAR(500) COMMENT 'Python 类路径：系统策略的实现类路径',
  `is_public` BIGINT UNSIGNED DEFAULT 0 COMMENT '是否公开：0-私有，1-公开',
  `status` VARCHAR(50) DEFAULT 'active' COMMENT '策略状态：active-活跃，inactive-停用',
  `created_by` VARCHAR(36) NOT NULL COMMENT '创建用户 ID：系统策略为system',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_strategy_id` (`strategy_id`),
  KEY `idx_strategy_type` (`strategy_type`),
  KEY `idx_status` (`status`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_strategy_name` (`strategy_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略表';

-- 创建策略-指标关联表
CREATE TABLE `strategy_indicators` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联 ID（主键）',
  `strategy_id` VARCHAR(36) NOT NULL COMMENT '策略 ID（外键）',
  `indicator_id` VARCHAR(36) NOT NULL COMMENT '指标 ID（外键）',
  `execution_order` BIGINT UNSIGNED NOT NULL COMMENT '执行顺序：指标在策略中的执行顺序',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_strategy_id` (`strategy_id`),
  KEY `idx_indicator_id` (`indicator_id`),
  KEY `idx_execution_order` (`execution_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略-指标关联表';

-- 创建策略-指标参数表
CREATE TABLE `strategy_indicators_params` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联 ID（主键）',
  `strategy_id` VARCHAR(36) NOT NULL COMMENT '策略 ID（外键）',
  `indicator_id` VARCHAR(36) NOT NULL COMMENT '指标 ID（外键）',
  `param_key` VARCHAR(100) NOT NULL COMMENT '参数键：参数名称',
  `param_value` TEXT COMMENT '参数值：参数值，支持不同类型',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_strategy_id` (`strategy_id`),
  KEY `idx_indicator_id` (`indicator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略-指标关联表';


-- 创建策略版本表
CREATE TABLE `strategy_versions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '版本 ID（主键）',
  `version_id` VARCHAR(36) NOT NULL COMMENT '版本唯一标识（UUID）',
  `strategy_id` VARCHAR(36) NOT NULL COMMENT '策略 ID（外键）',
  `version_number` VARCHAR(50) NOT NULL COMMENT '版本号：语义化版本号',
  `version_description` TEXT COMMENT '版本描述：版本的变更说明',
  `config_snapshot` TEXT NOT NULL COMMENT '配置快照：JSON 格式字符串，记录版本的完整配置',
  `created_by` VARCHAR(36) NOT NULL COMMENT '创建用户 ID：版本创建者',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_version_id` (`version_id`),
  KEY `idx_strategy_id` (`strategy_id`),
  KEY `idx_version_number` (`version_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略版本表';

-- 初始化完成
SELECT 'Database initialization completed successfully!' AS message;