const express = require("express");
const router = express.Router();
const { exec } = require("child_process");

// Restart selfheal-api pod
router.post("/restart", (req, res) => {
  exec("kubectl delete pod -n selfheal -l app=selfheal-api", (err, stdout, stderr) => {
    if (err) {
      return res.status(500).json({ error: stderr });
    }
    res.json({ message: "Restart triggered", output: stdout });
  });
});

module.exports = router;
