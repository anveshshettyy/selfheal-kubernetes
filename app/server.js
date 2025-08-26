import express from 'express';
import client from 'prom-client';

const app = express();
const PORT = process.env.PORT || 3000;

const register = new client.Registry();
client.collectDefaultMetrics({ register });

const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_seconds',
    help: 'HTTP request duration in seconds',
    labelNames: ['method', 'route', 'code'],
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
});
register.registerMetric(httpRequestDuration);

app.use((req, res, next) => {
    const end = httpRequestDuration.startTimer({ method: req.method });
    res.on('finish', () => end({ route: req.route?.path || req.path, code: res.statusCode }));
    next();
});

let ready = true;
app.get('/healthz', (req, res) => res.status(200).send('ok'));
app.get('/readyz', (req, res) => (ready ? res.send('ready') : res.status(503).send('not-ready')));
app.post('/toggle-ready', (req, res) => { ready = !ready; res.json({ ready }); });

app.get('/', (req, res) => {
    res.json({ service: 'selfheal-api', status: 'running' });
});

app.get('/work', (req, res) => {
    const ms = Math.min(parseInt(req.query.ms || '200', 10), 10000);
    const deadline  = Date.now() + ms;
    while(Date.now() < deadline) {
        Math.sqrt(Math.random());
    }
    res.json({ didWorkMs: ms });
});

const heap = [];
app.get('/leak', (req, res) => {
    const mb = Math.min(parseInt(req.query.mb || '10', 10), 200);
    const chunk = Buffer.alloc(mb * 1024 * 1024, 'a');
    heap.push(chunk);
    res.json({ leakedMB: mb, totalChunks: heap.length }); 
});

app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
});

app.listen(PORT, () => console.log(`selfheal-api listening on :${PORT}`));