import { Router } from 'express';
import { exec } from 'child_process';

const router = Router();

router.post("/restart", (req, res) => {
  console.log(`[ACTUATOR] Restart request received at ${new Date().toISOString()}`);
  exec("/usr/local/bin/kubectl delete pod -n selfheal -l app=selfheal-api", (err, stdout, stderr) => {
    if (err) {
      console.error(`[ACTUATOR ERROR]`, stderr);
      return res.status(500).json({ error: stderr });
    }
    console.log(`[ACTUATOR] Pods deleted:\n${stdout}`);
    res.json({ message: "Restart triggered", output: stdout });
  });
});

export default router;



