#!/bin/bash

# UX/UI Developer Role Testing Implementation
# Comprehensive design system, usability, accessibility, and user experience assessment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/ux_ui_developer"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[UX/UI Developer] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Design system assessment
run_design_system_tests() {
    log "Starting design system assessment"
    local design_issues=0
    local report_file="$RESULTS_DIR/design_system_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "design_system_assessment",
    "components": {
        "component_architecture": {},
        "styling_system": {},
        "typography": {},
        "color_system": {},
        "spacing_system": {}
    },
    "summary": {"issues": 0, "design_consistency": "unknown"}
}
EOF

    if [[ ! -d frontend/src ]]; then
        log "No frontend found, skipping design system testing"
        return 0
    fi
    
    # Component architecture analysis
    log "Analyzing component architecture"
    local comp_issues=0
    local comp_architecture=()
    
    # Component organization
    if [[ -d frontend/src/components ]]; then
        local component_count=$(find frontend/src/components -name "*.jsx" -o -name "*.tsx" | wc -l || echo "0")
        comp_architecture+=("React components: $component_count")
        log "React components: $component_count"
        
        if [[ $component_count -eq 0 ]]; then
            comp_issues=$((comp_issues + 1))
            comp_architecture+=("No React components found")
            log "⚠️ No React components found"
        fi
    else
        comp_issues=$((comp_issues + 1))
        comp_architecture+=("No components directory")
        log "⚠️ No components directory found"
    fi
    
    # Component reusability assessment
    if [[ -d frontend/src/components ]]; then
        # Check for common UI components
        local ui_components=("Button" "Input" "Modal" "Card" "Form" "Header" "Footer" "Navigation")
        local found_components=()
        local missing_components=()
        
        for comp in "${ui_components[@]}"; do
            if find frontend/src/components -name "*${comp}*" -o -name "*${comp,,}*" | head -1 >/dev/null 2>&1; then
                found_components+=("$comp")
            else
                missing_components+=("$comp")
            fi
        done
        
        comp_architecture+=("Common UI components found: ${found_components[*]}")
        log "✅ Found components: ${found_components[*]}"
        
        if [[ ${#missing_components[@]} -gt ${#ui_components[@]}/2 ]]; then
            comp_issues=$((comp_issues + 1))
            comp_architecture+=("Many common components missing: ${missing_components[*]}")
            log "⚠️ Missing components: ${missing_components[*]}"
        fi
    fi
    
    # Component composition patterns
    if [[ -d frontend/src/components ]]; then
        local composite_components=$(find frontend/src/components -name "*.jsx" -o -name "*.tsx" | xargs grep -l "children\|props\\.children" | wc -l || echo "0")
        local total_components=$(find frontend/src/components -name "*.jsx" -o -name "*.tsx" | wc -l || echo "1")
        local composition_ratio=$((composite_components * 100 / total_components))
        
        comp_architecture+=("Component composition ratio: ${composition_ratio}%")
        log "Component composition: ${composition_ratio}%"
        
        if [[ $composition_ratio -lt 30 ]]; then
            comp_issues=$((comp_issues + 1))
            comp_architecture+=("Low component composition usage")
            log "⚠️ Low component composition usage"
        fi
    fi
    
    local comp_json=$(printf '%s\n' "${comp_architecture[@]}" | jq -R . | jq -s .)
    jq --argjson architecture "$comp_json" --arg issues "$comp_issues" \
       '.components.component_architecture = {"issues": ($issues|tonumber), "architecture": $architecture}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    design_issues=$((design_issues + comp_issues))
    
    # Styling system analysis
    log "Analyzing styling system"
    local style_issues=0
    local styling_system=()
    
    # CSS organization
    local css_files=$(find frontend/src -name "*.css" -o -name "*.scss" -o -name "*.sass" -o -name "*.less" | wc -l || echo "0")
    local styled_components=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "styled-components\|emotion\|@emotion" | wc -l || echo "0")
    local css_modules=$(find frontend/src -name "*.module.css" -o -name "*.module.scss" | wc -l || echo "0")
    
    styling_system+=("CSS files: $css_files")
    styling_system+=("CSS-in-JS components: $styled_components")
    styling_system+=("CSS modules: $css_modules")
    log "Styling: $css_files CSS files, $styled_components CSS-in-JS, $css_modules modules"
    
    # CSS methodology assessment
    if [[ $css_files -gt 0 ]]; then
        local bem_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -c "__\|--" | awk '{sum+=$1} END {print sum}' || echo "0")
        if [[ $bem_usage -gt 10 ]]; then
            styling_system+=("BEM methodology detected")
            log "✅ BEM methodology usage detected"
        fi
    fi
    
    # CSS variable usage
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "var(--\|--.*:" >/dev/null 2>&1; then
        styling_system+=("CSS custom properties used")
        log "✅ CSS custom properties found"
    else
        style_issues=$((style_issues + 1))
        styling_system+=("No CSS custom properties found")
        log "⚠️ No CSS custom properties found"
    fi
    
    # Responsive design implementation
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "@media\|media query" >/dev/null 2>&1; then
        styling_system+=("Responsive design implemented")
        log "✅ Responsive design found"
    else
        style_issues=$((style_issues + 1))
        styling_system+=("No responsive design found")
        log "⚠️ No responsive design found"
    fi
    
    local style_json=$(printf '%s\n' "${styling_system[@]}" | jq -R . | jq -s .)
    jq --argjson system "$style_json" --arg issues "$style_issues" \
       '.components.styling_system = {"issues": ($issues|tonumber), "system": $system}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    design_issues=$((design_issues + style_issues))
    
    # Typography analysis
    log "Analyzing typography system"
    local type_issues=0
    local typography=()
    
    # Font loading and optimization
    if [[ -f frontend/index.html ]] && grep -q "font\|googleapis\|typekit" frontend/index.html; then
        typography+=("Web fonts loaded")
        log "✅ Web fonts found"
    else
        typography+=("No web fonts detected")
        log "ℹ️ No web fonts detected"
    fi
    
    # Typography scale
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "font-size\|text-.*:" >/dev/null 2>&1; then
        local font_sizes=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "font-size:[^;]*" | sort | uniq | wc -l || echo "0")
        typography+=("Font size variants: $font_sizes")
        log "Font size variants: $font_sizes"
        
        if [[ $font_sizes -gt 10 ]]; then
            type_issues=$((type_issues + 1))
            typography+=("Too many font size variants")
            log "⚠️ Too many font size variants"
        fi
    else
        type_issues=$((type_issues + 1))
        typography+=("No typography styles found")
        log "⚠️ No typography styles found"
    fi
    
    # Semantic text elements
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<h[1-6]\|<p>\|<span>\|<strong>\|<em>" >/dev/null 2>&1; then
        typography+=("Semantic text elements used")
        log "✅ Semantic text elements found"
    else
        type_issues=$((type_issues + 1))
        typography+=("No semantic text elements")
        log "⚠️ No semantic text elements found"
    fi
    
    # Typography consistency
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "line-height\|letter-spacing" >/dev/null 2>&1; then
        typography+=("Typography spacing configured")
        log "✅ Typography spacing found"
    else
        type_issues=$((type_issues + 1))
        typography+=("No typography spacing")
        log "⚠️ No typography spacing configured"
    fi
    
    local type_json=$(printf '%s\n' "${typography[@]}" | jq -R . | jq -s .)
    jq --argjson typography "$type_json" --arg issues "$type_issues" \
       '.components.typography = {"issues": ($issues|tonumber), "typography": $typography}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    design_issues=$((design_issues + type_issues))
    
    # Color system analysis
    log "Analyzing color system"
    local color_issues=0
    local color_system=()
    
    # Color variable usage
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "--.*color\|--.*bg\|--.*border" >/dev/null 2>&1; then
        local color_vars=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "--[^:]*color[^:]*:" | wc -l || echo "0")
        color_system+=("CSS color variables: $color_vars")
        log "✅ CSS color variables: $color_vars"
    else
        color_issues=$((color_issues + 1))
        color_system+=("No CSS color variables found")
        log "⚠️ No CSS color variables found"
    fi
    
    # Color consistency
    local hardcoded_colors=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "#[0-9a-fA-F]\{3,6\}\|rgb([^)]*)\|rgba([^)]*)" | sort | uniq | wc -l || echo "0")
    color_system+=("Hardcoded colors: $hardcoded_colors")
    log "Hardcoded colors: $hardcoded_colors"
    
    if [[ $hardcoded_colors -gt 20 ]]; then
        color_issues=$((color_issues + 1))
        color_system+=("Too many hardcoded colors")
        log "⚠️ Too many hardcoded colors"
    fi
    
    # Color accessibility
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "contrast\|accessibility\|a11y" >/dev/null 2>&1; then
        color_system+=("Color accessibility considerations found")
        log "✅ Color accessibility considerations found"
    else
        color_system+=("No color accessibility considerations")
        log "ℹ️ No color accessibility considerations found"
    fi
    
    # Dark mode support
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "dark\|theme\|prefers-color-scheme" >/dev/null 2>&1; then
        color_system+=("Dark mode support detected")
        log "✅ Dark mode support found"
    else
        color_system+=("No dark mode support")
        log "ℹ️ No dark mode support found"
    fi
    
    local color_json=$(printf '%s\n' "${color_system[@]}" | jq -R . | jq -s .)
    jq --argjson system "$color_json" --arg issues "$color_issues" \
       '.components.color_system = {"issues": ($issues|tonumber), "system": $system}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    design_issues=$((design_issues + color_issues))
    
    # Spacing system analysis
    log "Analyzing spacing system"
    local spacing_issues=0
    local spacing_system=()
    
    # Spacing variables
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "--.*spacing\|--.*margin\|--.*padding\|--.*gap" >/dev/null 2>&1; then
        local spacing_vars=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "--[^:]*\(spacing\|margin\|padding\|gap\)[^:]*:" | wc -l || echo "0")
        spacing_system+=("CSS spacing variables: $spacing_vars")
        log "✅ CSS spacing variables: $spacing_vars"
    else
        spacing_issues=$((spacing_issues + 1))
        spacing_system+=("No CSS spacing variables found")
        log "⚠️ No CSS spacing variables found"
    fi
    
    # Consistent spacing units
    local px_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "[0-9]\+px" | wc -l || echo "0")
    local rem_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "[0-9.]\+rem" | wc -l || echo "0")
    local em_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -o "[0-9.]\+em" | wc -l || echo "0")
    
    spacing_system+=("Spacing units - px: $px_usage, rem: $rem_usage, em: $em_usage")
    log "Spacing units - px: $px_usage, rem: $rem_usage, em: $em_usage"
    
    # Prefer relative units
    local total_units=$((px_usage + rem_usage + em_usage))
    if [[ $total_units -gt 0 ]]; then
        local relative_ratio=$(((rem_usage + em_usage) * 100 / total_units))
        spacing_system+=("Relative units usage: ${relative_ratio}%")
        log "Relative units usage: ${relative_ratio}%"
        
        if [[ $relative_ratio -lt 50 ]]; then
            spacing_issues=$((spacing_issues + 1))
            spacing_system+=("Low relative units usage")
            log "⚠️ Consider using more relative units"
        fi
    fi
    
    # Grid and flexbox usage
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "display:.*flex\|display:.*grid" >/dev/null 2>&1; then
        spacing_system+=("Modern layout methods used")
        log "✅ Flexbox/Grid layout found"
    else
        spacing_issues=$((spacing_issues + 1))
        spacing_system+=("No modern layout methods found")
        log "⚠️ No modern layout methods found"
    fi
    
    local spacing_json=$(printf '%s\n' "${spacing_system[@]}" | jq -R . | jq -s .)
    jq --argjson system "$spacing_json" --arg issues "$spacing_issues" \
       '.components.spacing_system = {"issues": ($issues|tonumber), "system": $system}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    design_issues=$((design_issues + spacing_issues))
    
    # Calculate design consistency
    local design_consistency="Excellent"
    if [[ $design_issues -eq 0 ]]; then
        design_consistency="Excellent"
    elif [[ $design_issues -le 2 ]]; then
        design_consistency="Good"
    elif [[ $design_issues -le 5 ]]; then
        design_consistency="Fair"
    else
        design_consistency="Poor"
    fi
    
    jq --arg issues "$design_issues" --arg consistency "$design_consistency" \
       '.summary.issues = ($issues|tonumber) | .summary.design_consistency = $consistency' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Design system assessment completed: $design_consistency ($design_issues issues)"
    return $([[ $design_issues -le 5 ]])  # Allow up to 5 design issues
}

# User interface quality assessment
run_ui_quality_tests() {
    log "Starting UI quality assessment"
    local ui_issues=0
    local report_file="$RESULTS_DIR/ui_quality_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "ui_quality_assessment",
    "quality": {
        "visual_hierarchy": {},
        "interaction_design": {},
        "layout_quality": {},
        "content_strategy": {}
    },
    "summary": {"issues": 0, "ui_score": 0}
}
EOF

    if [[ ! -d frontend/src ]]; then
        log "No frontend found, skipping UI quality testing"
        return 0
    fi
    
    # Visual hierarchy analysis
    log "Analyzing visual hierarchy"
    local hierarchy_issues=0
    local visual_hierarchy=()
    
    # Heading structure
    local heading_levels=()
    for level in {1..6}; do
        local count=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<h$level" | awk '{sum+=$1} END {print sum}' || echo "0")
        if [[ $count -gt 0 ]]; then
            heading_levels+=("h$level:$count")
        fi
    done
    
    if [[ ${#heading_levels[@]} -gt 0 ]]; then
        visual_hierarchy+=("Heading levels: ${heading_levels[*]}")
        log "✅ Heading levels: ${heading_levels[*]}"
        
        # Check for proper h1 usage
        local h1_count=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<h1" | awk '{sum+=$1} END {print sum}' || echo "0")
        if [[ $h1_count -eq 0 ]]; then
            hierarchy_issues=$((hierarchy_issues + 1))
            visual_hierarchy+=("No h1 elements found")
            log "⚠️ No h1 elements found"
        fi
    else
        hierarchy_issues=$((hierarchy_issues + 1))
        visual_hierarchy+=("No heading elements found")
        log "⚠️ No heading elements found"
    fi
    
    # Visual emphasis elements
    local emphasis_elements=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<strong>\|<em>\|<b>\|<i>" | awk '{sum+=$1} END {print sum}' || echo "0")
    visual_hierarchy+=("Text emphasis elements: $emphasis_elements")
    log "Text emphasis elements: $emphasis_elements"
    
    # Layout sections
    local section_elements=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<section>\|<article>\|<aside>\|<main>" | awk '{sum+=$1} END {print sum}' || echo "0")
    if [[ $section_elements -gt 0 ]]; then
        visual_hierarchy+=("Semantic sections: $section_elements")
        log "✅ Semantic sections: $section_elements"
    else
        hierarchy_issues=$((hierarchy_issues + 1))
        visual_hierarchy+=("No semantic sections found")
        log "⚠️ No semantic sections found"
    fi
    
    local hierarchy_json=$(printf '%s\n' "${visual_hierarchy[@]}" | jq -R . | jq -s .)
    jq --argjson hierarchy "$hierarchy_json" --arg issues "$hierarchy_issues" \
       '.quality.visual_hierarchy = {"issues": ($issues|tonumber), "hierarchy": $hierarchy}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ui_issues=$((ui_issues + hierarchy_issues))
    
    # Interaction design analysis
    log "Analyzing interaction design"
    local interaction_issues=0
    local interaction_design=()
    
    # Interactive elements
    local buttons=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<button\|type=[\"']button\|role=[\"']button" | awk '{sum+=$1} END {print sum}' || echo "0")
    local links=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<a\|<Link" | awk '{sum+=$1} END {print sum}' || echo "0")
    local inputs=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<input\|<textarea\|<select" | awk '{sum+=$1} END {print sum}' || echo "0")
    
    interaction_design+=("Interactive elements - buttons: $buttons, links: $links, inputs: $inputs")
    log "Interactive elements - buttons: $buttons, links: $links, inputs: $inputs"
    
    if [[ $buttons -eq 0 && $links -eq 0 ]]; then
        interaction_issues=$((interaction_issues + 1))
        interaction_design+=("No interactive elements found")
        log "⚠️ No interactive elements found"
    fi
    
    # Event handlers
    local event_handlers=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "onClick\|onSubmit\|onChange\|onFocus\|onBlur" | awk '{sum+=$1} END {print sum}' || echo "0")
    interaction_design+=("Event handlers: $event_handlers")
    log "Event handlers: $event_handlers"
    
    if [[ $event_handlers -eq 0 ]]; then
        interaction_issues=$((interaction_issues + 1))
        interaction_design+=("No event handlers found")
        log "⚠️ No event handlers found"
    fi
    
    # Loading states
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "loading\|spinner\|skeleton" >/dev/null 2>&1; then
        interaction_design+=("Loading states implemented")
        log "✅ Loading states found"
    else
        interaction_issues=$((interaction_issues + 1))
        interaction_design+=("No loading states found")
        log "⚠️ No loading states found"
    fi
    
    # Error states
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "error\|Error" >/dev/null 2>&1; then
        interaction_design+=("Error states implemented")
        log "✅ Error states found"
    else
        interaction_issues=$((interaction_issues + 1))
        interaction_design+=("No error states found")
        log "⚠️ No error states found"
    fi
    
    local interaction_json=$(printf '%s\n' "${interaction_design[@]}" | jq -R . | jq -s .)
    jq --argjson design "$interaction_json" --arg issues "$interaction_issues" \
       '.quality.interaction_design = {"issues": ($issues|tonumber), "design": $design}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ui_issues=$((ui_issues + interaction_issues))
    
    # Layout quality analysis
    log "Analyzing layout quality"
    local layout_issues=0
    local layout_quality=()
    
    # CSS layout methods
    local flexbox_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -c "display:.*flex\|flex-" | awk '{sum+=$1} END {print sum}' || echo "0")
    local grid_usage=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -c "display:.*grid\|grid-" | awk '{sum+=$1} END {print sum}' || echo "0")
    
    layout_quality+=("Layout methods - flexbox: $flexbox_usage, grid: $grid_usage")
    log "Layout methods - flexbox: $flexbox_usage, grid: $grid_usage"
    
    if [[ $flexbox_usage -eq 0 && $grid_usage -eq 0 ]]; then
        layout_issues=$((layout_issues + 1))
        layout_quality+=("No modern layout methods used")
        log "⚠️ No modern layout methods found"
    fi
    
    # Responsive design implementation
    local media_queries=$(find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -c "@media" | awk '{sum+=$1} END {print sum}' || echo "0")
    layout_quality+=("Media queries: $media_queries")
    log "Media queries: $media_queries"
    
    if [[ $media_queries -eq 0 ]]; then
        layout_issues=$((layout_issues + 1))
        layout_quality+=("No responsive design found")
        log "⚠️ No responsive design implementation"
    fi
    
    # Container and wrapper usage
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "container\|wrapper\|layout" >/dev/null 2>&1; then
        layout_quality+=("Layout containers used")
        log "✅ Layout containers found"
    else
        layout_issues=$((layout_issues + 1))
        layout_quality+=("No layout containers found")
        log "⚠️ No layout containers found"
    fi
    
    # Navigation structure
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<nav>\|navigation\|menu" >/dev/null 2>&1; then
        layout_quality+=("Navigation structure present")
        log "✅ Navigation structure found"
    else
        layout_issues=$((layout_issues + 1))
        layout_quality+=("No navigation structure found")
        log "⚠️ No navigation structure found"
    fi
    
    local layout_json=$(printf '%s\n' "${layout_quality[@]}" | jq -R . | jq -s .)
    jq --argjson quality "$layout_json" --arg issues "$layout_issues" \
       '.quality.layout_quality = {"issues": ($issues|tonumber), "quality": $quality}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ui_issues=$((ui_issues + layout_issues))
    
    # Content strategy analysis
    log "Analyzing content strategy"
    local content_issues=0
    local content_strategy=()
    
    # Content structure
    local paragraphs=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<p>" | awk '{sum+=$1} END {print sum}' || echo "0")
    local lists=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<ul>\|<ol>" | awk '{sum+=$1} END {print sum}' || echo "0")
    
    content_strategy+=("Content elements - paragraphs: $paragraphs, lists: $lists")
    log "Content elements - paragraphs: $paragraphs, lists: $lists"
    
    # Text content quality
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "lorem\|ipsum\|placeholder" >/dev/null 2>&1; then
        content_issues=$((content_issues + 1))
        content_strategy+=("Placeholder content found")
        log "⚠️ Placeholder content detected"
    else
        content_strategy+=("No placeholder content detected")
        log "✅ No placeholder content found"
    fi
    
    # Alt text for images
    local images=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "<img" | awk '{sum+=$1} END {print sum}' || echo "0")
    local alt_texts=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "alt=" | awk '{sum+=$1} END {print sum}' || echo "0")
    
    if [[ $images -gt 0 ]]; then
        local alt_ratio=$((alt_texts * 100 / images))
        content_strategy+=("Image alt text coverage: ${alt_ratio}%")
        log "Image alt text coverage: ${alt_ratio}%"
        
        if [[ $alt_ratio -lt 80 ]]; then
            content_issues=$((content_issues + 1))
            content_strategy+=("Low alt text coverage")
            log "⚠️ Low alt text coverage"
        fi
    else
        content_strategy+=("No images found")
        log "ℹ️ No images found"
    fi
    
    # Internationalization considerations
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "i18n\|translate\|locale" >/dev/null 2>&1; then
        content_strategy+=("Internationalization support found")
        log "✅ Internationalization support found"
    else
        content_strategy+=("No internationalization support")
        log "ℹ️ No internationalization support found"
    fi
    
    local content_json=$(printf '%s\n' "${content_strategy[@]}" | jq -R . | jq -s .)
    jq --argjson strategy "$content_json" --arg issues "$content_issues" \
       '.quality.content_strategy = {"issues": ($issues|tonumber), "strategy": $strategy}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ui_issues=$((ui_issues + content_issues))
    
    # Calculate UI score
    local total_categories=4
    local passed_categories=$((total_categories - ui_issues))
    local ui_score=$((passed_categories * 100 / total_categories))
    
    jq --arg issues "$ui_issues" --arg score "$ui_score" \
       '.summary.issues = ($issues|tonumber) | .summary.ui_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "UI quality assessment completed: Score ${ui_score}% ($ui_issues issues)"
    return $([[ $ui_issues -le 4 ]])  # Allow up to 4 UI issues
}

# User experience assessment
run_ux_tests() {
    log "Starting user experience assessment"
    local ux_issues=0
    local report_file="$RESULTS_DIR/ux_assessment_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "ux_assessment",
    "experience": {
        "user_flows": {},
        "accessibility": {},
        "performance_ux": {},
        "mobile_experience": {}
    },
    "summary": {"issues": 0, "ux_score": 0}
}
EOF

    if [[ ! -d frontend/src ]]; then
        log "No frontend found, skipping UX testing"
        return 0
    fi
    
    # User flows analysis
    log "Analyzing user flows"
    local flow_issues=0
    local user_flows=()
    
    # Navigation flow
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "navigate\|router\|Route\|Link" >/dev/null 2>&1; then
        user_flows+=("Navigation system implemented")
        log "✅ Navigation system found"
        
        # Check for breadcrumb navigation
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "breadcrumb\|crumb" >/dev/null 2>&1; then
            user_flows+=("Breadcrumb navigation present")
            log "✅ Breadcrumb navigation found"
        else
            user_flows+=("No breadcrumb navigation")
            log "ℹ️ No breadcrumb navigation found"
        fi
    else
        flow_issues=$((flow_issues + 1))
        user_flows+=("No navigation system found")
        log "⚠️ No navigation system found"
    fi
    
    # Form flow
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<form\|onSubmit" >/dev/null 2>&1; then
        user_flows+=("Form interactions present")
        log "✅ Form interactions found"
        
        # Form validation
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "validation\|error\|required" >/dev/null 2>&1; then
            user_flows+=("Form validation implemented")
            log "✅ Form validation found"
        else
            flow_issues=$((flow_issues + 1))
            user_flows+=("No form validation found")
            log "⚠️ No form validation found"
        fi
    else
        user_flows+=("No form interactions found")
        log "ℹ️ No form interactions found"
    fi
    
    # Search flow
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "search\|Search\|filter" >/dev/null 2>&1; then
        user_flows+=("Search functionality present")
        log "✅ Search functionality found"
    else
        user_flows+=("No search functionality")
        log "ℹ️ No search functionality found"
    fi
    
    # Error flow
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "ErrorBoundary\|error.*page\|404\|error.*state" >/dev/null 2>&1; then
        user_flows+=("Error handling flows present")
        log "✅ Error handling flows found"
    else
        flow_issues=$((flow_issues + 1))
        user_flows+=("No error handling flows found")
        log "⚠️ No error handling flows found"
    fi
    
    local flow_json=$(printf '%s\n' "${user_flows[@]}" | jq -R . | jq -s .)
    jq --argjson flows "$flow_json" --arg issues "$flow_issues" \
       '.experience.user_flows = {"issues": ($issues|tonumber), "flows": $flows}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ux_issues=$((ux_issues + flow_issues))
    
    # Accessibility assessment
    log "Analyzing accessibility implementation"
    local a11y_issues=0
    local accessibility=()
    
    # ARIA attributes
    local aria_labels=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "aria-label\|aria-labelledby\|aria-describedby" | awk '{sum+=$1} END {print sum}' || echo "0")
    accessibility+=("ARIA labels: $aria_labels")
    log "ARIA labels: $aria_labels"
    
    if [[ $aria_labels -eq 0 ]]; then
        a11y_issues=$((a11y_issues + 1))
        accessibility+=("No ARIA labels found")
        log "⚠️ No ARIA labels found"
    fi
    
    # Keyboard navigation
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "tabIndex\|onKeyDown\|onKeyPress" >/dev/null 2>&1; then
        accessibility+=("Keyboard navigation support")
        log "✅ Keyboard navigation support found"
    else
        a11y_issues=$((a11y_issues + 1))
        accessibility+=("No keyboard navigation support")
        log "⚠️ No keyboard navigation support"
    fi
    
    # Focus management
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "focus\|Focus\|autoFocus" >/dev/null 2>&1; then
        accessibility+=("Focus management implemented")
        log "✅ Focus management found"
    else
        a11y_issues=$((a11y_issues + 1))
        accessibility+=("No focus management found")
        log "⚠️ No focus management found"
    fi
    
    # Screen reader support
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "role=\|aria-\|sr-only\|screen.*reader" >/dev/null 2>&1; then
        accessibility+=("Screen reader support present")
        log "✅ Screen reader support found"
    else
        a11y_issues=$((a11y_issues + 1))
        accessibility+=("No screen reader support found")
        log "⚠️ No screen reader support found"
    fi
    
    local a11y_json=$(printf '%s\n' "${accessibility[@]}" | jq -R . | jq -s .)
    jq --argjson accessibility "$a11y_json" --arg issues "$a11y_issues" \
       '.experience.accessibility = {"issues": ($issues|tonumber), "accessibility": $accessibility}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ux_issues=$((ux_issues + a11y_issues))
    
    # Performance UX analysis
    log "Analyzing performance UX"
    local perf_issues=0
    local performance_ux=()
    
    # Loading optimization
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "lazy\|Suspense\|dynamic.*import" >/dev/null 2>&1; then
        performance_ux+=("Code splitting implemented")
        log "✅ Code splitting found"
    else
        perf_issues=$((perf_issues + 1))
        performance_ux+=("No code splitting found")
        log "⚠️ No code splitting found"
    fi
    
    # Image optimization
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "loading=[\"']lazy\|webp\|srcset" >/dev/null 2>&1; then
        performance_ux+=("Image optimization present")
        log "✅ Image optimization found"
    else
        performance_ux+=("No image optimization found")
        log "ℹ️ No image optimization found"
    fi
    
    # Progressive enhancement
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "fallback\|noscript\|progressive" >/dev/null 2>&1; then
        performance_ux+=("Progressive enhancement implemented")
        log "✅ Progressive enhancement found"
    else
        performance_ux+=("No progressive enhancement")
        log "ℹ️ No progressive enhancement found"
    fi
    
    # Performance monitoring
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "performance\|metrics\|vitals" >/dev/null 2>&1; then
        performance_ux+=("Performance monitoring present")
        log "✅ Performance monitoring found"
    else
        performance_ux+=("No performance monitoring")
        log "ℹ️ No performance monitoring found"
    fi
    
    local perf_json=$(printf '%s\n' "${performance_ux[@]}" | jq -R . | jq -s .)
    jq --argjson performance "$perf_json" --arg issues "$perf_issues" \
       '.experience.performance_ux = {"issues": ($issues|tonumber), "performance": $performance}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ux_issues=$((ux_issues + perf_issues))
    
    # Mobile experience analysis
    log "Analyzing mobile experience"
    local mobile_issues=0
    local mobile_experience=()
    
    # Responsive design
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "@media.*mobile\|@media.*768\|@media.*480" >/dev/null 2>&1; then
        mobile_experience+=("Mobile-specific media queries")
        log "✅ Mobile media queries found"
    else
        mobile_issues=$((mobile_issues + 1))
        mobile_experience+=("No mobile-specific media queries")
        log "⚠️ No mobile media queries found"
    fi
    
    # Touch optimization
    if find frontend/src -name "*.css" -o -name "*.scss" | xargs grep -l "touch\|44px\|48px" >/dev/null 2>&1; then
        mobile_experience+=("Touch target optimization")
        log "✅ Touch target optimization found"
    else
        mobile_issues=$((mobile_issues + 1))
        mobile_experience+=("No touch target optimization")
        log "⚠️ No touch target optimization"
    fi
    
    # Viewport configuration
    if [[ -f frontend/index.html ]] && grep -q "viewport" frontend/index.html; then
        mobile_experience+=("Viewport meta tag configured")
        log "✅ Viewport configuration found"
    else
        mobile_issues=$((mobile_issues + 1))
        mobile_experience+=("No viewport configuration")
        log "⚠️ No viewport configuration"
    fi
    
    # Mobile navigation
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "hamburger\|drawer\|mobile.*menu" >/dev/null 2>&1; then
        mobile_experience+=("Mobile navigation implemented")
        log "✅ Mobile navigation found"
    else
        mobile_issues=$((mobile_issues + 1))
        mobile_experience+=("No mobile navigation found")
        log "⚠️ No mobile navigation found"
    fi
    
    local mobile_json=$(printf '%s\n' "${mobile_experience[@]}" | jq -R . | jq -s .)
    jq --argjson experience "$mobile_json" --arg issues "$mobile_issues" \
       '.experience.mobile_experience = {"issues": ($issues|tonumber), "experience": $experience}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    ux_issues=$((ux_issues + mobile_issues))
    
    # Calculate UX score
    local total_categories=4
    local passed_categories=$((total_categories - ux_issues))
    local ux_score=$((passed_categories * 100 / total_categories))
    
    jq --arg issues "$ux_issues" --arg score "$ux_score" \
       '.summary.issues = ($issues|tonumber) | .summary.ux_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "UX assessment completed: Score ${ux_score}% ($ux_issues issues)"
    return $([[ $ux_issues -le 4 ]])  # Allow up to 4 UX issues
}

# Performance optimization assessment
run_performance_tests() {
    log "Starting performance optimization assessment"
    local perf_issues=0
    local report_file="$RESULTS_DIR/performance_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "performance_optimization_assessment",
    "optimization": {
        "bundle_optimization": {},
        "asset_optimization": {},
        "rendering_optimization": {},
        "caching_strategy": {}
    },
    "summary": {"issues": 0, "performance_score": 0}
}
EOF

    if [[ ! -d frontend ]]; then
        log "No frontend found, skipping performance testing"
        return 0
    fi
    
    # Bundle optimization analysis
    log "Analyzing bundle optimization"
    local bundle_issues=0
    local bundle_optimization=()
    
    # Build configuration
    if [[ -f frontend/vite.config.js ]] || [[ -f frontend/webpack.config.js ]] || [[ -f frontend/package.json ]]; then
        bundle_optimization+=("Build configuration present")
        log "✅ Build configuration found"
        
        # Check for optimization settings
        if [[ -f frontend/vite.config.js ]] && grep -q "build\|optimization\|minify" frontend/vite.config.js; then
            bundle_optimization+=("Build optimization configured")
            log "✅ Build optimization found"
        elif [[ -f frontend/package.json ]] && jq -e '.scripts.build' frontend/package.json >/dev/null 2>&1; then
            bundle_optimization+=("Build script configured")
            log "✅ Build script found"
        else
            bundle_issues=$((bundle_issues + 1))
            bundle_optimization+=("No build optimization found")
            log "⚠️ No build optimization found"
        fi
    else
        bundle_issues=$((bundle_issues + 1))
        bundle_optimization+=("No build configuration found")
        log "⚠️ No build configuration found"
    fi
    
    # Code splitting
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "lazy\|dynamic.*import\|import(.*)" >/dev/null 2>&1; then
        bundle_optimization+=("Code splitting implemented")
        log "✅ Code splitting found"
    else
        bundle_issues=$((bundle_issues + 1))
        bundle_optimization+=("No code splitting found")
        log "⚠️ No code splitting found"
    fi
    
    # Tree shaking
    if [[ -f frontend/package.json ]] && jq -e '.sideEffects' frontend/package.json >/dev/null 2>&1; then
        bundle_optimization+=("Tree shaking configuration")
        log "✅ Tree shaking configuration found"
    else
        bundle_optimization+=("No tree shaking configuration")
        log "ℹ️ No tree shaking configuration found"
    fi
    
    local bundle_json=$(printf '%s\n' "${bundle_optimization[@]}" | jq -R . | jq -s .)
    jq --argjson optimization "$bundle_json" --arg issues "$bundle_issues" \
       '.optimization.bundle_optimization = {"issues": ($issues|tonumber), "optimization": $optimization}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    perf_issues=$((perf_issues + bundle_issues))
    
    # Asset optimization analysis
    log "Analyzing asset optimization"
    local asset_issues=0
    local asset_optimization=()
    
    # Image optimization
    local image_files=$(find frontend -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.svg" | wc -l || echo "0")
    local webp_files=$(find frontend -name "*.webp" | wc -l || echo "0")
    
    if [[ $image_files -gt 0 ]]; then
        asset_optimization+=("Image assets: $image_files")
        log "Image assets: $image_files"
        
        if [[ $webp_files -gt 0 ]]; then
            asset_optimization+=("WebP optimization: $webp_files files")
            log "✅ WebP optimization found"
        else
            asset_optimization+=("No WebP optimization")
            log "ℹ️ No WebP optimization found"
        fi
    else
        asset_optimization+=("No image assets found")
        log "ℹ️ No image assets found"
    fi
    
    # Font optimization
    if [[ -d frontend/public ]] && find frontend/public -name "*.woff2" >/dev/null 2>&1; then
        asset_optimization+=("Font optimization (WOFF2)")
        log "✅ Font optimization found"
    else
        asset_optimization+=("No font optimization")
        log "ℹ️ No font optimization found"
    fi
    
    # CSS optimization
    if find frontend/src -name "*.css" -o -name "*.scss" | head -1 >/dev/null 2>&1; then
        local css_size=$(find frontend/src -name "*.css" -o -name "*.scss" -exec wc -c {} + | tail -1 | awk '{print $1}' || echo "0")
        asset_optimization+=("CSS size: ${css_size} bytes")
        log "CSS size: ${css_size} bytes"
        
        if [[ $css_size -gt 100000 ]]; then
            asset_issues=$((asset_issues + 1))
            asset_optimization+=("Large CSS files detected")
            log "⚠️ Large CSS files detected"
        fi
    fi
    
    local asset_json=$(printf '%s\n' "${asset_optimization[@]}" | jq -R . | jq -s .)
    jq --argjson optimization "$asset_json" --arg issues "$asset_issues" \
       '.optimization.asset_optimization = {"issues": ($issues|tonumber), "optimization": $optimization}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    perf_issues=$((perf_issues + asset_issues))
    
    # Rendering optimization analysis
    log "Analyzing rendering optimization"
    local rendering_issues=0
    local rendering_optimization=()
    
    # React optimization patterns
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "memo\|useMemo\|useCallback" >/dev/null 2>&1; then
        rendering_optimization+=("React optimization hooks used")
        log "✅ React optimization patterns found"
    else
        rendering_issues=$((rendering_issues + 1))
        rendering_optimization+=("No React optimization patterns")
        log "⚠️ No React optimization patterns found"
    fi
    
    # Virtual scrolling
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "virtual\|windowing" >/dev/null 2>&1; then
        rendering_optimization+=("Virtual scrolling implemented")
        log "✅ Virtual scrolling found"
    else
        rendering_optimization+=("No virtual scrolling")
        log "ℹ️ No virtual scrolling found"
    fi
    
    # Error boundaries
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "ErrorBoundary\|componentDidCatch" >/dev/null 2>&1; then
        rendering_optimization+=("Error boundaries implemented")
        log "✅ Error boundaries found"
    else
        rendering_issues=$((rendering_issues + 1))
        rendering_optimization+=("No error boundaries found")
        log "⚠️ No error boundaries found"
    fi
    
    # Suspense usage
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "Suspense" >/dev/null 2>&1; then
        rendering_optimization+=("Suspense for loading states")
        log "✅ Suspense implementation found"
    else
        rendering_optimization+=("No Suspense implementation")
        log "ℹ️ No Suspense implementation found"
    fi
    
    local rendering_json=$(printf '%s\n' "${rendering_optimization[@]}" | jq -R . | jq -s .)
    jq --argjson optimization "$rendering_json" --arg issues "$rendering_issues" \
       '.optimization.rendering_optimization = {"issues": ($issues|tonumber), "optimization": $optimization}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    perf_issues=$((perf_issues + rendering_issues))
    
    # Caching strategy analysis
    log "Analyzing caching strategy"
    local cache_issues=0
    local caching_strategy=()
    
    # Service worker
    if [[ -f frontend/public/sw.js ]] || find frontend/src -name "*worker*" >/dev/null 2>&1; then
        caching_strategy+=("Service worker present")
        log "✅ Service worker found"
    else
        caching_strategy+=("No service worker")
        log "ℹ️ No service worker found"
    fi
    
    # HTTP caching headers
    if [[ -f frontend/public/_headers ]] || [[ -f frontend/public/.htaccess ]]; then
        caching_strategy+=("HTTP caching configuration")
        log "✅ HTTP caching configuration found"
    else
        caching_strategy+=("No HTTP caching configuration")
        log "ℹ️ No HTTP caching configuration found"
    fi
    
    # Client-side caching
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "cache\|localStorage\|sessionStorage" >/dev/null 2>&1; then
        caching_strategy+=("Client-side caching implemented")
        log "✅ Client-side caching found"
    else
        cache_issues=$((cache_issues + 1))
        caching_strategy+=("No client-side caching")
        log "⚠️ No client-side caching found"
    fi
    
    # API caching
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "react-query\|swr\|apollo" >/dev/null 2>&1; then
        caching_strategy+=("API caching library used")
        log "✅ API caching library found"
    else
        caching_strategy+=("No API caching library")
        log "ℹ️ No API caching library found"
    fi
    
    local cache_json=$(printf '%s\n' "${caching_strategy[@]}" | jq -R . | jq -s .)
    jq --argjson strategy "$cache_json" --arg issues "$cache_issues" \
       '.optimization.caching_strategy = {"issues": ($issues|tonumber), "strategy": $strategy}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    perf_issues=$((perf_issues + cache_issues))
    
    # Calculate performance score
    local total_categories=4
    local optimized_categories=$((total_categories - perf_issues))
    local performance_score=$((optimized_categories * 100 / total_categories))
    
    jq --arg issues "$perf_issues" --arg score "$performance_score" \
       '.summary.issues = ($issues|tonumber) | .summary.performance_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Performance optimization assessment completed: Score ${performance_score}% ($perf_issues issues)"
    return $([[ $perf_issues -le 3 ]])  # Allow up to 3 performance issues
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting UX/UI Developer role testing: $test_name"
    
    case "$test_name" in
        "design_system_tests")
            run_design_system_tests
            ;;
        "ui_quality_tests")
            run_ui_quality_tests
            ;;
        "ux_tests")
            run_ux_tests
            ;;
        "performance_tests")
            run_performance_tests
            ;;
        "all")
            local overall_success=true
            
            run_design_system_tests || overall_success=false
            run_ui_quality_tests || overall_success=false
            run_ux_tests || overall_success=false
            run_performance_tests || overall_success=false
            
            if $overall_success; then
                log "✅ All UX/UI Developer tests passed"
                return 0
            else
                log "❌ Some UX/UI Developer tests failed"
                return 1
            fi
            ;;
        *)
            log "Unknown test: $test_name"
            return 1
            ;;
    esac
}

main "$@"