# TASKS.md Maintenance Guide

## Overview
This guide ensures TASKS.md stays current and accurate as the primary task tracking document for the whisper-transcriber project.

## Maintenance System

### Automated Maintenance Script
**Location**: `scripts/maintain_tasks.sh`

**Usage**:
```bash
# Update timestamps and status (run after any task changes)
./scripts/maintain_tasks.sh update

# Validate format only
./scripts/maintain_tasks.sh validate  

# Check current status
./scripts/maintain_tasks.sh status

# Show help
./scripts/maintain_tasks.sh help
```

### When to Update TASKS.md

#### **🔄 ROUTINE UPDATES** (Run `./scripts/maintain_tasks.sh update`)
- After completing any task
- After starting work on a new task  
- Weekly maintenance
- Before major project reviews

#### **✏️ MANUAL UPDATES** (Edit TASKS.md directly)
- Adding new issues or enhancements
- Changing task priorities
- Adding detailed implementation notes
- Updating acceptance criteria

#### **📊 STATUS CHANGES** (Update task headers)
- **Starting work**: Change to `🟡 **IN PROGRESS**`
- **Completing work**: Change to `✅ **COMPLETED**`
- **Blocking issues**: Add `🚫 **BLOCKED**` with reason

### Status Indicators

#### **Task Status Headers**
```markdown
#### **I001: Task Name** 🟡 **IN PROGRESS**
#### **~~I002: Completed Task~~** ✅ **COMPLETED**  
#### **I003: Task Name** 🚫 **BLOCKED** (reason)
#### **I004: Task Name** (no status = not started)
```

#### **Priority Indicators**
- 🔴 **CRITICAL**: Must fix before continued development
- 🟡 **HIGH**: Important for stability and quality
- 🟢 **MEDIUM**: Improvements and enhancements  
- ⚪ **LOW**: Nice-to-have features

### Maintenance Workflow

#### **Daily Development**
1. Check current focus: `./scripts/maintain_tasks.sh status`
2. Update task status when starting/completing work
3. Run maintenance: `./scripts/maintain_tasks.sh update`

#### **Weekly Reviews**
1. Review all task statuses
2. Archive completed tasks if section becomes large
3. Update priorities based on project needs
4. Add new issues/enhancements as discovered

#### **Project Milestones**
1. Comprehensive review of all tasks
2. Archive completed work to legacy section
3. Reassess priorities and timelines
4. Update project focus and next actions

## Integration with Development Workflow

### Git Workflow
```bash
# Before starting work
./scripts/maintain_tasks.sh status

# Update task status in TASKS.md (mark as IN PROGRESS)
# Do development work...

# After completing work  
./scripts/maintain_tasks.sh update
# Update task status in TASKS.md (mark as COMPLETED)
# Commit changes including updated TASKS.md
```

### CI/CD Integration
The maintenance script can be integrated into CI/CD pipelines:
```yaml
- name: Validate TASKS.md
  run: ./scripts/maintain_tasks.sh validate
```

## Current Status Tracking

### **Priority Focus System**
- **IMMEDIATE FOCUS**: Always displayed at top of TASKS.md
- **NEXT CRITICAL**: Next critical task to tackle
- **NEXT HIGH**: Next high-priority task

### **Progress Indicators**
- Task counts by priority level
- Completion percentages  
- In-progress work visibility
- Blocking issues identification

## Automation Features

### **Timestamp Management**
- Automatically updates "Last Updated" timestamp
- Tracks when maintenance was last performed

### **Status Counting**
- Counts completed, in-progress, and active tasks
- Updates status summary automatically
- Provides progress visibility

### **Format Validation**
- Ensures consistent task numbering
- Validates required sections exist
- Checks for proper markdown formatting

### **Next Action Suggestions**
- Identifies current focus areas
- Suggests next tasks to tackle
- Highlights priority work

## Best Practices

### **Task Documentation**
- Keep implementation steps detailed but concise
- Include file paths and technical context
- Update acceptance criteria as requirements evolve
- Document blockers and dependencies clearly

### **Status Management**
- Update status promptly when starting/completing work
- Use maintenance script for routine updates
- Keep focus on current and next priorities
- Archive completed work when sections become large

### **Team Coordination**
- Run maintenance before team reviews
- Share current focus with team members
- Update priorities based on team capacity
- Coordinate on task dependencies

---

**Last Updated**: 2025-10-22  
**Maintenance System**: ✅ Active  
**Next Review**: Weekly or as needed