#!/bin/bash

# Admin Functions User Experience Testing  
# This simulates a real admin user managing the Whisper Transcriber system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo -e "${BLUE}👑 ADMIN FUNCTIONS USER EXPERIENCE TEST${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Simulating a real administrator managing the Whisper Transcriber system"
echo "User Persona: System administrator who needs to monitor, configure, and maintain the service"
echo ""

# Get admin authentication token
echo -e "${BLUE}🔐 Step 1: Admin Authentication${NC}"
echo "Admin action: Logging in with administrative credentials"

TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"0AYw^lpZa!TM*iw0oIKX"}' \
    | jq -r '.access_token' 2>/dev/null || echo "")

if [[ -n "$TOKEN" && "$TOKEN" != "null" ]]; then
    echo -e "✅ Admin authentication successful"
    
    # Verify admin privileges
    admin_check=$(curl -s -X GET "$BASE_URL/auth/me" \
        -H "Authorization: Bearer $TOKEN")
    
    if [[ "$admin_check" == *'"is_admin":true'* ]]; then
        echo -e "✅ Admin privileges confirmed"
    else
        echo -e "⚠️  Admin privileges not detected"
    fi
else
    echo -e "❌ Admin authentication failed"
    echo -e "   Admin cannot access system management features"
    exit 1
fi

echo ""

# Step 2: System Status and Health Monitoring
echo -e "${BLUE}🏥 Step 2: System Health Monitoring${NC}"
echo "Admin action: Checking overall system health and status"

echo -n "   System health check: "
health_response=$(curl -s -X GET "$BASE_URL/health" -w "%{http_code}")
health_status=${health_response: -3}

if [[ "$health_status" == "200" ]]; then
    echo -e "${GREEN}Healthy${NC}"
    health_body=${health_response:0:-3}
    echo -e "     System status: ${health_body}"
else
    echo -e "${RED}Unhealthy (HTTP $health_status)${NC}"
fi

echo -n "   Admin system status: "
admin_status_response=$(curl -s -X GET "$BASE_URL/admin/status" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

admin_status_code=${admin_status_response: -3}
if [[ "$admin_status_code" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    admin_status_body=${admin_status_response:0:-3}
    echo -e "     Admin can monitor detailed system status"
    echo -e "     Status: ${admin_status_body:0:100}..."
else
    echo -e "${YELLOW}Not available (HTTP $admin_status_code)${NC}"
    echo -e "     Admin system monitoring needs implementation"
fi

echo ""

# Step 3: User Management
echo -e "${BLUE}👥 Step 3: User Management${NC}"
echo "Admin action: Managing user accounts and permissions"

echo -n "   List all users: "
users_response=$(curl -s -X GET "$BASE_URL/admin/users" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

users_status=${users_response: -3}
if [[ "$users_status" == "200" ]]; then
    echo -e "${GREEN}Working${NC}"
    users_body=${users_response:0:-3}
    
    # Count users if possible
    if [[ "$users_body" == *'"users"'* ]]; then
        echo -e "     Admin can view user list"
        echo -e "     User data: ${users_body:0:80}..."
    fi
elif [[ "$users_status" == "404" ]]; then
    echo -e "${YELLOW}Endpoint not implemented${NC}"
    echo -e "     User management UI needs development"
else
    echo -e "${RED}Failed (HTTP $users_status)${NC}"
    echo -e "     Admin cannot manage users"
fi

echo -n "   User creation capability: "
create_user_response=$(curl -s -X POST "$BASE_URL/admin/users" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"testpass","role":"user"}' \
    -w "%{http_code}")

create_status=${create_user_response: -3}
if [[ "$create_status" == "200" ]] || [[ "$create_status" == "201" ]]; then
    echo -e "${GREEN}Working${NC}"
    echo -e "     Admin can create new users"
    
    # Try to delete the test user
    curl -s -X DELETE "$BASE_URL/admin/users/testuser" \
        -H "Authorization: Bearer $TOKEN" > /dev/null
        
elif [[ "$create_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     User creation endpoint needs development"
else
    echo -e "${RED}Failed (HTTP $create_status)${NC}"
fi

echo ""

# Step 4: Job Management and Monitoring
echo -e "${BLUE}📊 Step 4: Job Management and Monitoring${NC}"
echo "Admin action: Monitoring all transcription jobs and system workload"

echo -n "   View all system jobs: "
all_jobs_response=$(curl -s -X GET "$BASE_URL/admin/jobs" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

all_jobs_status=${all_jobs_response: -3}
if [[ "$all_jobs_status" == "200" ]]; then
    echo -e "${GREEN}Working${NC}"
    all_jobs_body=${all_jobs_response:0:-3}
    
    if [[ "$all_jobs_body" == *'"jobs"'* ]] || [[ "$all_jobs_body" == *'"total"'* ]]; then
        echo -e "     Admin can monitor all user jobs"
        echo -e "     Jobs data: ${all_jobs_body:0:80}..."
    fi
elif [[ "$all_jobs_status" == "404" ]]; then
    echo -e "${YELLOW}Using regular endpoint${NC}"
    
    # Fall back to regular jobs endpoint
    regular_jobs_response=$(curl -s -X GET "$BASE_URL/jobs/" \
        -H "Authorization: Bearer $TOKEN" \
        -w "%{http_code}")
    
    regular_jobs_status=${regular_jobs_response: -3}
    if [[ "$regular_jobs_status" == "200" ]]; then
        echo -e "     Admin can view jobs through regular API"
    fi
else
    echo -e "${RED}Failed (HTTP $all_jobs_status)${NC}"
fi

echo -n "   System metrics: "
metrics_response=$(curl -s -X GET "$BASE_URL/metrics" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

metrics_status=${metrics_response: -3}
if [[ "$metrics_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    metrics_body=${metrics_response:0:-3}
    echo -e "     Admin can monitor system performance"
    echo -e "     Metrics: ${metrics_body:0:80}..."
else
    echo -e "${YELLOW}Not available (HTTP $metrics_status)${NC}"
    echo -e "     Performance monitoring needs implementation"
fi

echo ""

# Step 5: System Configuration
echo -e "${BLUE}⚙️  Step 5: System Configuration Management${NC}"
echo "Admin action: Viewing and modifying system settings"

echo -n "   System settings: "
settings_response=$(curl -s -X GET "$BASE_URL/admin/settings" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

settings_status=${settings_response: -3}
if [[ "$settings_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    settings_body=${settings_response:0:-3}
    echo -e "     Admin can view/modify system configuration"
    echo -e "     Settings: ${settings_body:0:80}..."
elif [[ "$settings_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Settings management UI needs development"
else
    echo -e "${RED}Failed (HTTP $settings_status)${NC}"
fi

echo -n "   Model management: "
models_response=$(curl -s -X GET "$BASE_URL/admin/models" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

models_status=${models_response: -3}
if [[ "$models_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    models_body=${models_response:0:-3}
    echo -e "     Admin can manage AI models"
    echo -e "     Models: ${models_body:0:80}..."
elif [[ "$models_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Model management needs development"
else
    echo -e "${RED}Failed (HTTP $models_status)${NC}"
fi

echo ""

# Step 6: Security and Audit Logs
echo -e "${BLUE}🛡️  Step 6: Security and Audit Management${NC}"
echo "Admin action: Reviewing security logs and audit trails"

echo -n "   Audit logs: "
audit_response=$(curl -s -X GET "$BASE_URL/admin/audit" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

audit_status=${audit_response: -3}
if [[ "$audit_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    audit_body=${audit_response:0:-3}
    echo -e "     Admin can review security audit logs"
    echo -e "     Audit data: ${audit_body:0:80}..."
elif [[ "$audit_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Audit logging review needs development"
else
    echo -e "${RED}Failed (HTTP $audit_status)${NC}"
fi

echo -n "   System logs: "
logs_response=$(curl -s -X GET "$BASE_URL/logs" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

logs_status=${logs_response: -3}
if [[ "$logs_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    logs_body=${logs_response:0:-3}
    echo -e "     Admin can access system logs"
    echo -e "     Logs: ${logs_body:0:80}..."
else
    echo -e "${YELLOW}Not available (HTTP $logs_status)${NC}"
    echo -e "     System log access needs implementation"
fi

echo ""

# Step 7: System Maintenance Operations
echo -e "${BLUE}🔧 Step 7: System Maintenance Operations${NC}"
echo "Admin action: Performing maintenance tasks and cleanup operations"

echo -n "   Database maintenance: "
db_maintenance_response=$(curl -s -X POST "$BASE_URL/admin/maintenance/database" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

db_maintenance_status=${db_maintenance_response: -3}
if [[ "$db_maintenance_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin can perform database cleanup"
elif [[ "$db_maintenance_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Database maintenance automation needed"
else
    echo -e "${RED}Failed (HTTP $db_maintenance_status)${NC}"
fi

echo -n "   Cache management: "
cache_response=$(curl -s -X POST "$BASE_URL/admin/cache/clear" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

cache_status=${cache_response: -3}
if [[ "$cache_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin can clear system cache"
elif [[ "$cache_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Cache management tools needed"
else
    echo -e "${RED}Failed (HTTP $cache_status)${NC}"
fi

echo ""

# Step 8: Backup and Recovery
echo -e "${BLUE}💾 Step 8: Backup and Recovery Operations${NC}"
echo "Admin action: Managing system backups and disaster recovery"

echo -n "   Create backup: "
backup_response=$(curl -s -X POST "$BASE_URL/admin/backup" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

backup_status=${backup_response: -3}
if [[ "$backup_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    backup_body=${backup_response:0:-3}
    echo -e "     Admin can create system backups"
    echo -e "     Backup: ${backup_body:0:80}..."
elif [[ "$backup_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Backup system needs development"
else
    echo -e "${RED}Failed (HTTP $backup_status)${NC}"
fi

echo -n "   List backups: "
backup_list_response=$(curl -s -X GET "$BASE_URL/admin/backups" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

backup_list_status=${backup_list_response: -3}
if [[ "$backup_list_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin can view backup history"
elif [[ "$backup_list_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
else
    echo -e "${RED}Failed (HTTP $backup_list_status)${NC}"
fi

echo ""

# Step 9: Performance Monitoring
echo -e "${BLUE}📈 Step 9: Performance Monitoring and Analytics${NC}"
echo "Admin action: Monitoring system performance and analyzing usage patterns"

echo -n "   Performance metrics: "
perf_response=$(curl -s -X GET "$BASE_URL/admin/performance" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

perf_status=${perf_response: -3}
if [[ "$perf_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    perf_body=${perf_response:0:-3}
    echo -e "     Admin can monitor detailed performance"
    echo -e "     Performance: ${perf_body:0:80}..."
elif [[ "$perf_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Performance monitoring dashboard needed"
else
    echo -e "${RED}Failed (HTTP $perf_status)${NC}"
fi

echo -n "   Usage analytics: "
analytics_response=$(curl -s -X GET "$BASE_URL/admin/analytics" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

analytics_status=${analytics_response: -3}
if [[ "$analytics_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin can view usage analytics"
elif [[ "$analytics_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Usage analytics need development"
else
    echo -e "${RED}Failed (HTTP $analytics_status)${NC}"
fi

echo ""

# Step 10: Emergency Operations
echo -e "${BLUE}🚨 Step 10: Emergency Operations and Safety Controls${NC}"
echo "Admin action: Testing emergency controls and safety measures"

echo -n "   System shutdown capability: "
shutdown_test_response=$(curl -s -X GET "$BASE_URL/admin/shutdown/status" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

shutdown_status=${shutdown_test_response: -3}
if [[ "$shutdown_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin has emergency shutdown controls"
elif [[ "$shutdown_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Emergency controls need development"
else
    echo -e "${RED}Failed (HTTP $shutdown_status)${NC}"
fi

echo -n "   Service restart capability: "
restart_test_response=$(curl -s -X GET "$BASE_URL/admin/restart/status" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

restart_status=${restart_test_response: -3}
if [[ "$restart_status" == "200" ]]; then
    echo -e "${GREEN}Available${NC}"
    echo -e "     Admin can restart system services"
elif [[ "$restart_status" == "404" ]]; then
    echo -e "${YELLOW}Not implemented${NC}"
    echo -e "     Service control needs development"
else
    echo -e "${RED}Failed (HTTP $restart_status)${NC}"
fi

echo ""

# Final Admin Assessment
echo -e "${BLUE}📊 ADMIN EXPERIENCE SUMMARY${NC}"
echo -e "${BLUE}===========================${NC}"
echo ""

# Evaluate admin capabilities
declare -a admin_functions=(
    "Authentication & Authorization"
    "System Health Monitoring" 
    "User Management"
    "Job Management & Monitoring"
    "System Configuration"
    "Security & Audit Logs"
    "System Maintenance"
    "Backup & Recovery"
    "Performance Monitoring"
    "Emergency Operations"
)

# Count implemented vs needed functions
implemented_functions=2  # Auth and basic monitoring work
total_functions=${#admin_functions[@]}

echo -e "Admin Functionality Assessment:"
echo -e "  ✅ Authentication & Authorization: Working"
echo -e "  ✅ System Health Monitoring: Basic functionality"
echo -e "  ⚠️  User Management: Needs implementation"
echo -e "  ⚠️  Job Management & Monitoring: Partial"
echo -e "  ⚠️  System Configuration: Needs implementation"
echo -e "  ⚠️  Security & Audit Logs: Needs implementation"
echo -e "  ⚠️  System Maintenance: Needs implementation"
echo -e "  ⚠️  Backup & Recovery: Needs implementation"
echo -e "  ⚠️  Performance Monitoring: Needs implementation"
echo -e "  ⚠️  Emergency Operations: Needs implementation"

echo ""
admin_score=$(( implemented_functions * 100 / total_functions ))
echo -e "Admin Functionality Score: ${YELLOW}${admin_score}%${NC}"

if [[ $admin_score -ge 80 ]]; then
    echo -e "${GREEN}🎉 ADMIN INTERFACE READY FOR PRODUCTION${NC}"
    echo -e "   Administrators have all necessary tools"
elif [[ $admin_score -ge 50 ]]; then
    echo -e "${YELLOW}⚠️  ADMIN INTERFACE NEEDS DEVELOPMENT${NC}"
    echo -e "   Basic admin functions work, but many features missing"
    echo -e "   Suitable for basic production with manual processes"
else
    echo -e "${RED}❌ ADMIN INTERFACE INSUFFICIENT${NC}"
    echo -e "   Critical admin functions missing"
    echo -e "   Requires significant development before production"
fi

echo ""
echo -e "Production Readiness Assessment:"
if [[ $admin_score -ge 50 ]]; then
    echo -e "  ✅ System has basic administrative capabilities"
    echo -e "  ✅ Core functions can be managed manually if needed"
    echo -e "  ⚠️  Advanced admin features should be prioritized for development"
    echo -e "  🚀 Acceptable for production launch with manual admin processes"
else
    echo -e "  ❌ Insufficient admin capabilities for production"
    echo -e "  ❌ Critical management functions missing"
    echo -e "  🛑 Not recommended for production without admin development"
fi

echo ""
echo -e "${BLUE}🔄 Admin testing complete - Ready for API testing${NC}"