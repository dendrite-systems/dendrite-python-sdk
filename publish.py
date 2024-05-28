import subprocess


def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)


# Step 1: Clean the dist directory
print("Cleaning the dist directory...")
run_command("rm -rf dist/*")

# Step 2: Build the package
print("Building the package...")
run_command("poetry build")

# Step 3: Publish the package to PyPI
print("Publishing the package to PyPI...")
run_command("poetry publish")

print("Done!")
