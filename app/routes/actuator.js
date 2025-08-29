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


// import * as k8s from '@kubernetes/client-node';
// import { Router } from 'express';

// const router = Router();

// // Initialize Kubernetes client using in-cluster configuration
// const kc = new k8s.KubeConfig();
// kc.loadFromCluster(); // uses ServiceAccount token automatically
// const k8sApi = kc.makeApiClient(k8s.CoreV1Api);

// router.post("/restart", async (req, res) => {
//   console.log(`[ACTUATOR] Restart request received at ${new Date().toISOString()}`);

//   try {
//     // List pods with the label app=selfheal-api in namespace selfheal
//     const pods = await k8sApi.listNamespacedPod('selfheal', undefined, undefined, undefined, undefined, 'app=selfheal-api');

//     // Delete all matching pods
//     const deletePromises = pods.body.items.map(pod =>
//       k8sApi.deleteNamespacedPod(pod.metadata.name, 'selfheal')
//     );

//     const results = await Promise.all(deletePromises);

//     console.log(`[ACTUATOR] Pods deleted:`, results.map(r => r.body?.status || 'deleted'));

//     res.json({ message: "Restart triggered", output: results.map(r => r.body?.status || 'deleted') });
//   } catch (err) {
//     console.error(`[ACTUATOR ERROR]`, err);
//     res.status(500).json({ error: err.message });
//   }
// });

// export default router;


