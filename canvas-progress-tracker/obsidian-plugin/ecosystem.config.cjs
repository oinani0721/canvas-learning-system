// PM2 ecosystem config for esbuild watch
// 启动: pm2 start ecosystem.config.cjs
// 停止: pm2 stop canvas-plugin-watch
// 日志: pm2 logs canvas-plugin-watch
// 状态: pm2 status

module.exports = {
  apps: [{
    name: 'canvas-plugin-watch',
    script: 'esbuild.config.mjs',
    cwd: __dirname,
    interpreter: 'node',
    watch: false,  // esbuild 自己有 watch，PM2 不需要重复
    autorestart: true,
    max_restarts: 10,
    restart_delay: 2000,
    env: {
      NODE_ENV: 'development'
    }
  }]
};
