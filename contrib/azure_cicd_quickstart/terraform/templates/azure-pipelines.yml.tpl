trigger:
  batch: false
  branches:
    include:
    - dev
    - test
    - main
  paths:
    exclude:
      - README.md
      - LICENSE
      - .github

pr:
  branches:
    include:
    - '*'
  paths:
    exclude:
      - README.md
      - LICENSE
      - .github

variables:
  # Dynamic variable group selection based on target branch for PRs and source branch for pushes
  
  # For Pull Requests: Use target branch to determine variable group
  - ${{ if and(eq(variables['Build.Reason'], 'PullRequest'), eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/main')) }}:
    - group: PIPELINE_NAME_PROD
  - ${{ if and(eq(variables['Build.Reason'], 'PullRequest'), eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/test')) }}:
    - group: PIPELINE_NAME_TEST
  - ${{ if and(eq(variables['Build.Reason'], 'PullRequest'), eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/dev')) }}:
    - group: PIPELINE_NAME_DEV
  - ${{ if and(eq(variables['Build.Reason'], 'PullRequest'), not(or(eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/main'), eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/test'), eq(variables['System.PullRequest.TargetBranch'], 'refs/heads/dev')))) }}:
    - group: PIPELINE_NAME_DEV
  
  # For Direct Pushes: Use source branch to determine variable group
  - ${{ if and(ne(variables['Build.Reason'], 'PullRequest'), eq(variables['Build.SourceBranchName'], 'main')) }}:
    - group: PIPELINE_NAME_PROD
  - ${{ if and(ne(variables['Build.Reason'], 'PullRequest'), eq(variables['Build.SourceBranchName'], 'test')) }}:
    - group: PIPELINE_NAME_TEST
  - ${{ if and(ne(variables['Build.Reason'], 'PullRequest'), eq(variables['Build.SourceBranchName'], 'dev')) }}:
    - group: PIPELINE_NAME_DEV
  - ${{ if and(ne(variables['Build.Reason'], 'PullRequest'), not(or(eq(variables['Build.SourceBranchName'], 'main'), eq(variables['Build.SourceBranchName'], 'test'), eq(variables['Build.SourceBranchName'], 'dev')))) }}:
    - group: PIPELINE_NAME_DEV

stages:
# Stage 1: Detect changed DAB folders
- stage: DetectChanges
  jobs:
  - job: DetectChangedDABs
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - checkout: self
      fetchDepth: 0  # Fetch full history for git diff
      displayName: 'Checkout with full history'
    
    - script: |
        echo "Detecting changed DAB folders..."
        
        # Get the target branch for comparison (main or master)
        TARGET_BRANCH="origin/main"
        if ! git show-ref --verify --quiet refs/remotes/origin/main; then
          TARGET_BRANCH="origin/master"
        fi
        
        echo "Comparing against: $TARGET_BRANCH"
        
        # Determine the correct comparison point based on commit type
        echo "Current HEAD: $(git rev-parse HEAD)"
        
        # Check if current commit is a merge commit
        if git rev-parse --verify HEAD^2 >/dev/null 2>&1; then
          # This is a merge commit, compare against first parent (previous state of target branch)
          COMPARE_AGAINST="HEAD^1"
          echo "Merge commit detected, comparing against first parent: $(git rev-parse HEAD^1)"
        else
          # Regular commit, compare against previous commit
          COMPARE_AGAINST="HEAD~1"
          echo "Regular commit, comparing against previous commit: $(git rev-parse HEAD~1)"
        fi
        
        echo "Comparing changes from $COMPARE_AGAINST to HEAD"
        
        # Find all folders in all root directories that have a databricks.yml file
        ALL_DABS=$(find . -maxdepth 7 -name "databricks.yml" -type f | sed 's|/databricks.yml||' | sed 's|^\./||' | sort)
        echo "All DAB folders found:"
        echo "$ALL_DABS"
        
        # Find changed DAB folders and create list
        CHANGED_DABS_LIST=""
        CHANGED_COUNT=0
        
        for dab_folder in $ALL_DABS; do
          # Check if any files in this DAB folder have changed
          CHANGES=$(git diff --name-only $COMPARE_AGAINST HEAD -- "$dab_folder/" | wc -l)
          if [ $CHANGES -gt 0 ]; then
            echo "Changes detected in: $dab_folder ($CHANGES files changed)"
            echo "  Changed files:"
            git diff --name-only $COMPARE_AGAINST HEAD -- "$dab_folder/" | sed 's/^/    /'
            CHANGED_COUNT=$((CHANGED_COUNT + 1))
            
            if [ -z "$CHANGED_DABS_LIST" ]; then
              CHANGED_DABS_LIST="$dab_folder"
            else
              CHANGED_DABS_LIST="$CHANGED_DABS_LIST,$dab_folder"
            fi
          else
            echo "No changes in: $dab_folder"
          fi
        done
        
        if [ $CHANGED_COUNT -eq 0 ]; then
          echo "No DAB folders have changes"
          echo "##vso[task.setvariable variable=CHANGED_DABS;isOutput=true]"
          echo "##vso[task.setvariable variable=HAS_CHANGES;isOutput=true]false"
          echo "##vso[task.setvariable variable=CHANGED_COUNT;isOutput=true]0"
        else
          echo ""
          echo "========================================="
          echo "SUMMARY: $CHANGED_COUNT DAB(s) with changes"
          echo "========================================="
          echo "$CHANGED_DABS_LIST" | tr ',' '\n' | nl -w2 -s'. '
          echo "========================================="
          echo ""
          echo "##vso[task.setvariable variable=CHANGED_DABS;isOutput=true]$CHANGED_DABS_LIST"
          echo "##vso[task.setvariable variable=HAS_CHANGES;isOutput=true]true"
          echo "##vso[task.setvariable variable=CHANGED_COUNT;isOutput=true]$CHANGED_COUNT"
        fi
      name: detectChanges
      displayName: 'Detect changed DAB folders'

# Stage 2: Deploy changed DABs sequentially (push to dev/test/main only)
- stage: DeployChangedDABs
  condition: ne(variables['Build.Reason'], 'PullRequest')
  dependsOn: DetectChanges
  jobs:
  - job: DeployDABsSequentially
    pool:
      vmImage: 'ubuntu-latest'
    timeoutInMinutes: 120  # Increase timeout for multiple DABs
    variables:
      changed_dabs: $[ stageDependencies.DetectChanges.DetectChangedDABs.outputs['detectChanges.CHANGED_DABS'] ]
      changed_count: $[ stageDependencies.DetectChanges.DetectChangedDABs.outputs['detectChanges.CHANGED_COUNT'] ]
    
    steps:
    - script: |
        echo "Job started successfully!"
        echo "changed_dabs value: '$(changed_dabs)'"
        echo "changed_count value: '$(changed_count)'"
        echo "=== ENVIRONMENT DEBUG ==="
        echo "Build.Reason: $(Build.Reason)"
        echo "Build.SourceBranchName: $(Build.SourceBranchName)"
        echo "System.PullRequest.TargetBranch: $(System.PullRequest.TargetBranch)"
        echo "env variable: $(env)"
        echo "DATABRICKS_HOST: $(DATABRICKS_HOST)"
        echo "SERVICE_CONNECTION_NAME: $(SERVICE_CONNECTION_NAME)"
        echo "=========================="
      displayName: 'Job Start Confirmation and Debug Info'
    
    - script: |
        # Enhanced check for changes with better logging
        CHANGED_COUNT="$(changed_count)"
        CHANGED_DABS="$(changed_dabs)"
        
        echo "=== DEPLOYMENT CHECK ==="
        echo "Changed count from job variable: '$CHANGED_COUNT'"
        echo "Changed DABs list: '$CHANGED_DABS'"
        
        # Check if we have any changes (multiple conditions for robustness)
        if [ -z "$CHANGED_COUNT" ] || [ "$CHANGED_COUNT" = "0" ] || [ "$CHANGED_COUNT" = "" ] || [ -z "$CHANGED_DABS" ] || [ "$CHANGED_DABS" = "" ]; then
          echo ""
          echo "##[section]No DAB changes detected - skipping all deployment tasks"
          echo "##vso[task.setvariable variable=SKIP_DEPLOYMENT;isOutput=true]true"
          echo "##vso[task.complete result=Succeeded;]No changes to deploy"
          exit 0
        fi
        
        echo ""
        echo "=== DEPLOYMENT OVERVIEW ==="
        echo "Total DABs to deploy: $CHANGED_COUNT"
        echo "Environment: $(env)"
        echo "Databricks Host: $(DATABRICKS_HOST)"
        echo ""
        echo "DABs to be deployed:"
        echo "$CHANGED_DABS" | tr ',' '\n' | nl -w2 -s'. '
        echo "=================================="
        echo "##vso[task.setvariable variable=SKIP_DEPLOYMENT;isOutput=true]false"
      displayName: 'Check for changes and deployment overview'
      name: checkChanges
    
    - task: UsePythonVersion@0
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      displayName: 'Use Python 3.10'
      inputs:
        versionSpec: '3.10'
    
    - task: AzureCLI@2
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      inputs:
        azureSubscription: $(SERVICE_CONNECTION_NAME)
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          echo "Getting access token..."
          DATABRICKS_TOKEN=$(az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d --query "accessToken" -o tsv)
          echo "##vso[task.setvariable variable=DATABRICKS_TOKEN]$DATABRICKS_TOKEN"
      displayName: 'Get Databricks Token'
        
    - checkout: self
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      displayName: 'Checkout repository'

    - script: |
        # Install uv (faster method)
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        
        # Create virtual environment and install dependencies with optimizations
        echo "Creating virtual environment with uv..."
        uv venv .venv --python $(which python)
        
        echo "Installing Python dependencies with uv..."
        # Install dependencies with standard uv (no binary restrictions)
        source .venv/bin/activate && \
        uv pip install \
          nutter \
          wheel \
          setuptools \
          pytest \
          pyspark
        
        # Make the virtual environment available for subsequent steps
        echo "##vso[task.setvariable variable=VIRTUAL_ENV]$(pwd)/.venv"
        echo "##vso[task.setvariable variable=PATH]$(pwd)/.venv/bin:$PATH"
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      displayName: 'Install Python dependencies with uv (optimized)'
      
    - script: |
        echo "Installing Databricks CLI..."
        curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
        
        # Ensure we use the newer CLI version
        export PATH="/usr/local/bin:$PATH"
        echo "Using Databricks CLI at: $(which databricks)"
        databricks --version
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      displayName: 'Install Databricks CLI'
    
    - script: |
        echo "Configuring Databricks CLI..."
        export PATH="/usr/local/bin:$PATH"
        
        # Test databricks auth
        echo "Testing databricks authentication..."
        databricks auth describe
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      env:
        DATABRICKS_HOST: $(DATABRICKS_HOST)
        DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)
      displayName: 'Configure and test Databricks CLI'
    
    - script: |
        echo "Starting sequential DAB deployment..."
        echo "=================================="
        
        # Ensure we use the correct Databricks CLI version
        export PATH="/usr/local/bin:$PATH"
        
        # Split the comma-separated list of DABs
        IFS=',' read -ra DABS_ARRAY <<< "$(changed_dabs)"
        
        # Initialize counters
        TOTAL_DABS=${#DABS_ARRAY[@]}
        CURRENT_DAB=0
        SUCCESS_COUNT=0
        FAILED_COUNT=0
        FAILED_DABS=""
        
        # Process each DAB
        for DAB_FOLDER in "${DABS_ARRAY[@]}"; do
          CURRENT_DAB=$((CURRENT_DAB + 1))
          
          echo ""
          echo "##[section]========================================="
          echo "##[section]Processing DAB $CURRENT_DAB of $TOTAL_DABS: $DAB_FOLDER"
          echo "##[section]========================================="
          
          # Validate directory exists
          if [ ! -d "$DAB_FOLDER" ]; then
            echo "##[error]Directory $DAB_FOLDER does not exist!"
            echo "[$CURRENT_DAB/$TOTAL_DABS] $DAB_FOLDER - FAILED (Directory not found)"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_DABS="$FAILED_DABS\n  - $DAB_FOLDER (Directory not found)"
            continue
          fi
          
          # Change to DAB directory
          cd "$DAB_FOLDER"
          
          # Validate databricks.yml exists
          if [ ! -f "databricks.yml" ]; then
            echo "##[error]databricks.yml not found in $DAB_FOLDER!"
            echo "[$CURRENT_DAB/$TOTAL_DABS] $DAB_FOLDER - FAILED (databricks.yml not found)"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_DABS="$FAILED_DABS\n  - $DAB_FOLDER (databricks.yml not found)"
            cd /home/vsts/work/1/s
            continue
          fi
          
          # Validate bundle
          echo ""
          echo "##[group]Validating bundle..."
          echo "Running: databricks bundle validate -t $(env)"
          echo "Environment variables:"
          echo "  DATABRICKS_HOST: $(DATABRICKS_HOST)"
          echo "  Target environment: $(env)"
          echo "  Working directory: $(pwd)"
          echo ""
          
          # Show databricks.yml content for debugging
          echo "databricks.yml content:"
          cat databricks.yml | head -50
          echo ""
          
          if databricks bundle validate -t $(env); then
            echo "✓ Validation successful"
            echo "##[endgroup]"
          else
            VALIDATION_EXIT_CODE=$?
            echo "##[error]Validation failed for $DAB_FOLDER with exit code: $VALIDATION_EXIT_CODE"
            echo "##[error]Re-running validation with maximum verbosity for debugging:"
            databricks bundle validate -t $(env) --debug || true
            echo "##[endgroup]"
            echo "[$CURRENT_DAB/$TOTAL_DABS] $DAB_FOLDER - FAILED (Validation error - exit code: $VALIDATION_EXIT_CODE)"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_DABS="$FAILED_DABS\n  - $DAB_FOLDER (Validation error - exit code: $VALIDATION_EXIT_CODE)"
            cd /home/vsts/work/1/s
            continue
          fi
          
          # Deploy bundle
          echo ""
          echo "##[group]Deploying bundle..."
          if databricks bundle deploy -t $(env); then
            echo "✓ Deployment successful"
            echo "##[endgroup]"
            echo "[$CURRENT_DAB/$TOTAL_DABS] $DAB_FOLDER - SUCCESS"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
          else
            echo "##[error]Deployment failed for $DAB_FOLDER!"
            echo "##[endgroup]"
            echo "[$CURRENT_DAB/$TOTAL_DABS] $DAB_FOLDER - FAILED (Deployment error)"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_DABS="$FAILED_DABS\n  - $DAB_FOLDER (Deployment error)"
          fi
          
          # Return to root directory
          cd /home/vsts/work/1/s
          
          echo ""
          echo "Progress: $CURRENT_DAB/$TOTAL_DABS completed (Success: $SUCCESS_COUNT, Failed: $FAILED_COUNT)"
          echo "========================================="
        done
        
        # Final summary
        echo ""
        echo "##[section]========================================="
        echo "##[section]DEPLOYMENT COMPLETE"
        echo "##[section]========================================="
        echo "Total DABs processed: $TOTAL_DABS"
        echo "Successful: $SUCCESS_COUNT"
        echo "Failed: $FAILED_COUNT"
        
        echo "End Time: $(date)"
        echo "Total: $TOTAL_DABS | Success: $SUCCESS_COUNT | Failed: $FAILED_COUNT"
        
        # Set output variables for summary stage
        echo "##vso[task.setvariable variable=DEPLOYMENT_SUMMARY;isOutput=true]"
        echo "##vso[task.setvariable variable=SUCCESS_COUNT;isOutput=true]$SUCCESS_COUNT"
        echo "##vso[task.setvariable variable=FAILED_COUNT;isOutput=true]$FAILED_COUNT"
        
        # Fail the job if any DAB failed
        if [ $FAILED_COUNT -gt 0 ]; then
          echo ""
          echo "##[error]$FAILED_COUNT DAB(s) failed to deploy:"
          echo -e "$FAILED_DABS"
          echo ""
          echo "##vso[task.logissue type=error]$FAILED_COUNT out of $TOTAL_DABS DAB deployments failed"
          exit 1
        else
          echo ""
          echo "##[section]All DABs deployed successfully! 🎉"
        fi
      condition: ne(variables['checkChanges.SKIP_DEPLOYMENT'], 'true')
      env:
        DATABRICKS_HOST: $(DATABRICKS_HOST)
        DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)
      name: deployAll
      displayName: 'Deploy all changed bundles sequentially'

# Stage 3: Summary and notifications
- stage: Summary
  condition: always()
  dependsOn: 
  - DetectChanges
  - DeployChangedDABs
  jobs:
  - job: PublishResults
    pool:
      vmImage: 'ubuntu-latest'
    variables:
      has_changes: $[ stageDependencies.DetectChanges.DetectChangedDABs.outputs['detectChanges.HAS_CHANGES'] ]
      changed_count: $[ stageDependencies.DetectChanges.DetectChangedDABs.outputs['detectChanges.CHANGED_COUNT'] ]
      deploy_success_count: $[ stageDependencies.DeployChangedDABs.DeployDABsSequentially.outputs['deployAll.SUCCESS_COUNT'] ]
      deploy_failed_count: $[ stageDependencies.DeployChangedDABs.DeployDABsSequentially.outputs['deployAll.FAILED_COUNT'] ]
    steps:
    - script: |
        echo "=== PIPELINE SUMMARY ==="
        echo "========================"
        
        if [ "$(has_changes)" = "false" ]; then
          echo "No DAB changes detected."
        else
          echo "Changed DABs: $(changed_count)"
          
          # Check if this was a PR or deployment
          if [ "$(System.PullRequest.PullRequestId)" != "" ]; then
            echo "Pull Request - Changes detected but no deployment performed."
          else
            echo "Deployment Results:"
            if [ -n "$(deploy_success_count)" ]; then
              echo "  Successfully deployed: $(deploy_success_count)"
            fi
            if [ -n "$(deploy_failed_count)" ]; then
              echo "  Failed deployments: $(deploy_failed_count)"
            fi
            
            if [ -n "$(deploy_failed_count)" ] && [ "$(deploy_failed_count)" -gt 0 ]; then
              echo ""
              echo "##vso[task.logissue type=error]Pipeline completed with $(deploy_failed_count) failed deployment(s)"
            fi
          fi
        fi
        
        echo ""
        echo "Check the stage logs for detailed information."
      displayName: 'Pipeline Summary'
    
    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: '**/test-*.xml' 
        failTaskOnFailedTests: false
      displayName: 'Publish test results'