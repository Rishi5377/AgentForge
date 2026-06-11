const { execSync } = require('child_process');

if (process.env.VERCEL === '1') {
  console.log('Vercel environment detected. Pulling Git LFS files...');
  try {
    // Vercel already has git-lfs installed.
    // We just need to ensure the remote origin is set properly if it isn't.
    execSync('git lfs install', { stdio: 'inherit' });
    execSync('git lfs pull', { stdio: 'inherit' });
    console.log('Git LFS pull successful.');
  } catch (error) {
    console.error('Failed to pull Git LFS:', error.message);
    process.exit(1);
  }
} else {
  console.log('Local environment detected. Skipping Git LFS pull.');
}
