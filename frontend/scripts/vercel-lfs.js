const { execSync } = require('child_process');

if (process.env.VERCEL === '1') {
  console.log('Vercel environment detected. Installing and pulling Git LFS...');
  try {
    execSync('yum install git-lfs -y', { stdio: 'inherit' });
    execSync('git lfs pull', { stdio: 'inherit' });
    console.log('Git LFS pull successful.');
  } catch (error) {
    console.error('Failed to pull Git LFS:', error.message);
    process.exit(1);
  }
} else {
  console.log('Local environment detected. Skipping Git LFS install.');
}
