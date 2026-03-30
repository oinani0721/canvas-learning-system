#!/bin/bash
# Canvas Learning System - Claude Dev Container Firewall
# Default-deny + whitelist for approved destinations only

iptables -F && iptables -P OUTPUT DROP

# Loopback
iptables -A OUTPUT -o lo -j ACCEPT
# Established connections
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Anthropic API
iptables -A OUTPUT -d api.anthropic.com -j ACCEPT

# Package managers
iptables -A OUTPUT -d registry.npmjs.org -j ACCEPT
iptables -A OUTPUT -d pypi.org -j ACCEPT
iptables -A OUTPUT -d files.pythonhosted.org -j ACCEPT

# GitHub
iptables -A OUTPUT -d github.com -j ACCEPT
iptables -A OUTPUT -d objects.githubusercontent.com -j ACCEPT

# Rust/Tauri crate registry
iptables -A OUTPUT -d crates.io -j ACCEPT
iptables -A OUTPUT -d static.crates.io -j ACCEPT

# HuggingFace/Ollama model downloads
iptables -A OUTPUT -d huggingface.co -j ACCEPT
iptables -A OUTPUT -d cdn-lfs.huggingface.co -j ACCEPT

# Docker internal networks
iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT

echo "Firewall: default-deny + whitelist active"
