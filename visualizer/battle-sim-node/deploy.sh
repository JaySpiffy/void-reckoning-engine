#!/bin/bash

# =============================================================================
# DARWIN'S ISLAND REHELIXED - DEPLOYMENT SCRIPT
# =============================================================================
# 
# This script deploys the built Vite app to a remote server via SSH/SCP.
# It uses tar+scp as a fallback since rsync is not available on all servers.
#
# REQUIREMENTS:
#   - SSH access configured in ~/.ssh/config
#   - jq installed locally (for JSON parsing)
#   - SSH key authentication set up
#
# USAGE:
#   ./deploy.sh              # Full build and deploy
#   ./deploy.sh --skip-build # Deploy without rebuilding
#   ./deploy.sh --dry-run    # Show what would be done
#
# CONFIGURATION:
#   Edit deploy-config.json to change server settings
#
# TROUBLESHOOTING:
#   - If build fails with TypeScript errors, run: npx vite build
#   - If SSH fails, check: ssh myserver "echo test"
#   - For 404 errors after deploy, verify base path in vite.config.ts
#
# =============================================================================

CONFIG_FILE="deploy-config.json"
SKIP_BUILD=false
DRY_RUN=false

# Colors for output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
MAGENTA='\033[1;35m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Darwin's Island Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-build    Skip the npm build process"
    echo "  --dry-run       Show what would be done without making changes"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh              # Full build and deploy"
    echo "  ./deploy.sh --skip-build # Deploy current dist/ without rebuilding"
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build) SKIP_BUILD=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# Load config with jq
get_config() {
    jq -r ".$1" "$CONFIG_FILE"
}

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: $CONFIG_FILE not found${NC}"
    exit 1
fi

SERVER_ALIAS=$(get_config "serverAlias")
REMOTE_ROOT=$(get_config "remoteWebRoot")
LOCAL_DIR=$(get_config "localSiteDir")
SITE_URL=$(get_config "siteUrl")

echo -e "${BLUE}>>> Deploying Darwin's Island to $SITE_URL${NC}"

# Step 1: Build
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${GREEN}Step 1: Building project...${NC}"
    echo -e "${YELLOW}Note: If TypeScript errors occur, you can build manually with:${NC}"
    echo -e "${YELLOW}      npx vite build${NC}"
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}Build failed!${NC}"
        echo -e "${YELLOW}Try running: npx vite build${NC}"
        exit 1
    fi
fi

# Step 2: Test SSH
echo -e "${GREEN}Step 2: Checking connection to $SERVER_ALIAS...${NC}"
ssh -o ConnectTimeout=5 "$SERVER_ALIAS" "echo 'Connected'" > /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}SSH connection failed. Check your ~/.ssh/config for '$SERVER_ALIAS'${NC}"
    exit 1
fi

# Step 3: Deploy via tar+scp (rsync fallback)
echo -e "${GREEN}Step 3: Uploading files to $REMOTE_ROOT...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would:"
    echo "  1. Create dist.tar.gz from $LOCAL_DIR/"
    echo "  2. scp dist.tar.gz to $SERVER_ALIAS:$REMOTE_ROOT/"
    echo "  3. Extract on server and set permissions"
else
    # Create tarball
    echo "  Creating archive..."
    tar -czf dist.tar.gz -C "$LOCAL_DIR" .
    
    # Ensure remote directory exists
    ssh "$SERVER_ALIAS" "mkdir -p $REMOTE_ROOT"
    
    # Upload
    echo "  Uploading archive..."
    scp dist.tar.gz "$SERVER_ALIAS:$REMOTE_ROOT/"
    
    # Extract and cleanup on server
    echo "  Extracting on server..."
    ssh "$SERVER_ALIAS" "cd $REMOTE_ROOT && tar -xzf dist.tar.gz && rm dist.tar.gz"
    
    # Cleanup locally
    rm -f dist.tar.gz
fi

# Step 4: Post-deploy commands from config
echo -e "${GREEN}Step 4: Running post-deployment commands...${NC}"
if [ "$DRY_RUN" = false ]; then
    # Read commands from config and execute them one by one
    readarray -t COMMANDS < <(jq -r '.postDeploy.commands[]' "$CONFIG_FILE")
    for cmd in "${COMMANDS[@]}"; do
        echo "  Executing: $cmd"
        ssh "$SERVER_ALIAS" "$cmd"
    done
fi

# Step 5: Verify deployment
echo -e "${GREEN}Step 5: Verifying deployment...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✓ Site is accessible (HTTP 200)${NC}"
else
    echo -e "  ${YELLOW}⚠ Site returned HTTP $HTTP_STATUS${NC}"
fi

echo -e "${MAGENTA}Deployment Complete! View at: $SITE_URL${NC}"
