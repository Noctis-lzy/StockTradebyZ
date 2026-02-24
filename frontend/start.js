import { createServer } from 'vite';

async function start() {
  try {
    const server = await createServer({
      configFile: './vite.config.js',
      server: {
        port: 3000
      }
    });
    
    await server.listen();
    console.log('Frontend server started on http://localhost:3000');
  } catch (error) {
    console.error('Failed to start frontend server:', error);
  }
}

start();
