CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 1aea27fe0d54

CREATE TABLE chart_results (
    chart_type VARCHAR(50) NOT NULL COMMENT '圖形類別', 
    params_json JSON NOT NULL COMMENT '參數', 
    params_figure JSON NOT NULL COMMENT '圖表大項', 
    cache_key VARCHAR(100) NOT NULL COMMENT '唯一索引', 
    status ENUM('PENDING','READY','FAILED') NOT NULL COMMENT '產製狀態', 
    create_by INTEGER COMMENT '建立者ID', 
    create_at DATETIME COMMENT '建立時間' DEFAULT now(), 
    update_at DATETIME COMMENT '更新時間' DEFAULT now(), 
    id INTEGER NOT NULL COMMENT 'ID主鍵' AUTO_INCREMENT, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_chart_results_cache_key ON chart_results (cache_key);

CREATE TABLE chart_requests (
    chart_type VARCHAR(50) NOT NULL COMMENT '圖形類別', 
    params_json JSON NOT NULL COMMENT '參數', 
    cache_hit BOOL NOT NULL COMMENT '是否命中快取', 
    result_id INTEGER COMMENT '結果ID', 
    create_at DATETIME COMMENT '查詢時間' DEFAULT now(), 
    id INTEGER NOT NULL COMMENT 'ID主鍵' AUTO_INCREMENT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(result_id) REFERENCES chart_results (id) ON DELETE CASCADE
);

INSERT INTO alembic_version (version_num) VALUES ('1aea27fe0d54');

-- Running upgrade 1aea27fe0d54 -> bdc8a023725f

ALTER TABLE chart_requests ADD COLUMN test VARCHAR(30);

UPDATE alembic_version SET version_num='bdc8a023725f' WHERE alembic_version.version_num = '1aea27fe0d54';

