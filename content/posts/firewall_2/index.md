+++
date = '2025-06-22T01:03:32+08:00'
draft = true
title = '那些防火墙的事情（2）'
+++

之前我写了一篇防火墙的文，那篇东西还是比较基础。经过详细了解社团的网络架构之后，我又有了很多收获。接下来会详细介绍一下我新学到的东西！

还是从这张表开始讲起...
{{< mermaid >}}

graph TD
    %% --- 整体布局定义 ---
    subgraph "入口"
        A_IN["物理网卡 接收"]
    end

    subgraph "PREROUTING - 路由前"
        B_PRE("PREROUTING")
        B_PRE --> C_RAW["table: raw"]
        C_RAW --> D_MANGLE["table: mangle"]
        D_MANGLE --> E_NAT["table: nat (DST-NAT) 端口转发"]
    end

    A_IN --> B_PRE
    E_NAT --> F_ROUTE1["第一次路由决策"]

    %% --- 核心处理路径 (水平布局) ---
    subgraph "核心处理路径"
        direction RL

        subgraph "INPUT - 发往路由器"
            G_INPUT("INPUT")
            G_INPUT --> H_MANGLE_IN["table: mangle"]
            H_MANGLE_IN --> I_FILTER_IN["table: filter"]
            I_FILTER_IN --> J_LOCAL["路由器<br>本地进程"]
        end

        subgraph "FORWARD - 转发"
            K_FORWARD("FORWARD")
            K_FORWARD --> L_MANGLE_FWD["table: mangle"]
            L_MANGLE_FWD --> M_FILTER_FWD["table: filter"]
        end
        
        subgraph "OUTPUT - 由路由器发出"
            N_OUTPUT("OUTPUT")
            N_OUTPUT --> O_ROUTE2["第二次<br>路由决策"]
            O_ROUTE2 --> P_RAW_OUT["table: raw"]
            P_RAW_OUT --> Q_MANGLE_OUT["table: mangle"]
            Q_MANGLE_OUT --> R_NAT_OUT["table: nat (DST-NAT)"]
            R_NAT_OUT --> S_FILTER_OUT["table: filter"]
        end
    end

    %% --- 路径连接 ---
    F_ROUTE1 -- "目标: 路由器" --> G_INPUT
    F_ROUTE1 -- "目标: 需转发" --> K_FORWARD
    J_LOCAL --> N_OUTPUT

    subgraph "POSTROUTING - 路由后"
        T_POST("POSTROUTING")
        T_POST --> U_MANGLE_POST["table: mangle"]
        U_MANGLE_POST --> V_NAT_POST["table: nat (SRC-NAT)<br>地址伪装"]
    end
    
    M_FILTER_FWD --> T_POST
    S_FILTER_OUT --> T_POST

    subgraph "出口"
        W_OUT["物理网卡 发送"]
    end
    
    V_NAT_POST --> W_OUT

    %% --- 样式定义 (最基础、最兼容的逐条定义) ---
    %% 即使渲染器不支持style, 图表结构依然能正确显示
    
    %% 入口/出口/决策点/本地进程 的特殊样式
    style A_IN fill:#f9f,stroke:#333
    style W_OUT fill:#f9f,stroke:#333
    style F_ROUTE1 fill:#D2B4DE,stroke:#333
    style O_ROUTE2 fill:#D2B4DE,stroke:#333
    style J_LOCAL fill:#A9DFBF,stroke:#333

    %% raw 表 (红色系)
    style C_RAW fill:#FFB3B3,stroke:#990000
    style P_RAW_OUT fill:#FFB3B3,stroke:#990000
    
    %% mangle 表 (橙色系)
    style D_MANGLE fill:#FFE0B3,stroke:#E67E22
    style H_MANGLE_IN fill:#FFE0B3,stroke:#E67E22
    style L_MANGLE_FWD fill:#FFE0B3,stroke:#E67E22
    style Q_MANGLE_OUT fill:#FFE0B3,stroke:#E67E22
    style U_MANGLE_POST fill:#FFE0B3,stroke:#E67E22

    %% nat 表 (蓝色系)
    style E_NAT fill:#B3D9FF,stroke:#3498DB
    style R_NAT_OUT fill:#B3D9FF,stroke:#3498DB
    style V_NAT_POST fill:#B3D9FF,stroke:#3498DB

    %% filter 表 (绿色系)
    style I_FILTER_IN fill:#B3FFCB,stroke:#2ECC71
    style M_FILTER_FWD fill:#B3FFCB,stroke:#2ECC71
    style S_FILTER_OUT fill:#B3FFCB,stroke:#2ECC71

{{< /mermaid >}}

