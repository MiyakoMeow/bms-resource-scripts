use std::{
    collections::{HashMap, HashSet},
    path::Path,
};

use regex::Regex;
use smol::{fs, io, stream::StreamExt};

use crate::fs::moving::{move_elements_across_dir, replace_options_update_pack};

// Japanese hiragana
static RE_JAPANESE_HIRAGANA: once_cell::sync::Lazy<Regex> =
    once_cell::sync::Lazy::new(|| Regex::new(r"[\u{3040}-\u{309f}]+").unwrap());
// Japanese katakana
static RE_JAPANESE_KATAKANA: once_cell::sync::Lazy<Regex> =
    once_cell::sync::Lazy::new(|| Regex::new(r"[\u{30a0}-\u{30ff}]+").unwrap());
// Chinese characters
static RE_CHINESE_CHARACTER: once_cell::sync::Lazy<Regex> =
    once_cell::sync::Lazy::new(|| Regex::new(r"[\u{4e00}-\u{9fa5}]+").unwrap());

#[derive(Debug, Clone)]
struct FirstCharRule {
    name: &'static str,
    func: fn(&str) -> bool,
}

const FIRST_CHAR_RULES: &[FirstCharRule] = &[
    FirstCharRule {
        name: "0-9",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| c.is_ascii_digit())
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "ABCD",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| ('A'..='D').contains(&c.to_ascii_uppercase()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "EFGHIJK",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| ('E'..='K').contains(&c.to_ascii_uppercase()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "LMNOPQ",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| ('L'..='Q').contains(&c.to_ascii_uppercase()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "RST",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| ('R'..='T').contains(&c.to_ascii_uppercase()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "UVWXYZ",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| ('U'..='Z').contains(&c.to_ascii_uppercase()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "平假",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| RE_JAPANESE_HIRAGANA.is_match(&c.to_string()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "片假",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| RE_JAPANESE_KATAKANA.is_match(&c.to_string()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "字",
        func: |name: &str| {
            name.chars()
                .next()
                .map(|c| RE_CHINESE_CHARACTER.is_match(&c.to_string()))
                .unwrap_or(false)
        },
    },
    FirstCharRule {
        name: "+",
        func: |name: &str| !name.is_empty(),
    },
];

fn first_char_rules_find(name: &str) -> &'static str {
    for rule in FIRST_CHAR_RULES {
        if (rule.func)(name) {
            return rule.name;
        }
    }
    "Uncategorized"
}

/// Split works in this directory into multiple folders according to first character
pub async fn split_folders_with_first_char(root_dir: impl AsRef<Path>) -> io::Result<()> {
    let root_dir = root_dir.as_ref();
    let root_folder_name = root_dir
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| io::Error::other("Invalid directory name"))?;

    if !root_dir.is_dir() {
        return Err(io::Error::other(format!(
            "{} is not a dir!",
            root_dir.display()
        )));
    }

    if root_dir.to_string_lossy().ends_with(']') {
        return Err(io::Error::other(format!(
            "{} endswith ']'. Aborting...",
            root_dir.display()
        )));
    }

    let parent_dir = root_dir
        .parent()
        .ok_or_else(|| io::Error::other("No parent directory"))?;

    let mut entries = fs::read_dir(root_dir).await?;
    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let element_path = entry.path();
        let element_name = entry.file_name().to_string_lossy().to_string();

        // Find target dir
        let rule = first_char_rules_find(&element_name);
        let target_dir = parent_dir.join(format!("{root_folder_name} [{rule}]"));

        if !target_dir.exists() {
            fs::create_dir(&target_dir).await?;
        }

        // Move
        let target_path = target_dir.join(&element_name);
        fs::rename(&element_path, &target_path).await?;
    }

    Ok(())
}

/// (Undo operation) Split works in this directory into multiple folders according to first character
pub async fn undo_split_pack(root_dir: impl AsRef<Path>) -> io::Result<()> {
    let root_dir = root_dir.as_ref();
    let root_folder_name = root_dir
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| io::Error::other("Invalid directory name"))?;

    let parent_dir = root_dir
        .parent()
        .ok_or_else(|| io::Error::other("No parent directory"))?;

    let mut pairs = Vec::new();
    let mut entries = fs::read_dir(parent_dir).await?;

    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let folder_path = entry.path();
        let folder_name = entry.file_name().to_string_lossy().to_string();

        if folder_name.starts_with(&format!("{root_folder_name} [")) && folder_name.ends_with(']') {
            println!(" - {} <- {}", root_dir.display(), folder_path.display());
            pairs.push((folder_path, root_dir.to_path_buf()));
        }
    }

    if pairs.is_empty() {
        println!("No folders to merge found.");
        return Ok(());
    }

    println!("Found {} folders to merge. Confirm? [y/N]", pairs.len());
    let mut input = String::new();
    std::io::stdin().read_line(&mut input)?;

    if !input.trim().to_lowercase().starts_with('y') {
        println!("Operation cancelled.");
        return Ok(());
    }

    for (from_dir, to_dir) in pairs {
        move_elements_across_dir(
            &from_dir,
            &to_dir,
            Default::default(),
            replace_options_update_pack(),
        )
        .await?;
    }

    Ok(())
}

/// Merge split folders
pub async fn merge_split_folders(root_dir: impl AsRef<Path>) -> io::Result<()> {
    let root_dir = root_dir.as_ref();
    let mut dir_names = Vec::new();
    let mut entries = fs::read_dir(root_dir).await?;

    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir()
            && let Some(name) = path.file_name().and_then(|n| n.to_str())
        {
            dir_names.push(name.to_string());
        }
    }

    let mut pairs = Vec::new();

    for dir_name in &dir_names {
        let dir_path = root_dir.join(dir_name);
        if !dir_path.is_dir() {
            continue;
        }

        // Situation 1: endswith "]"
        if dir_name.ends_with(']') {
            // Find dir_name_without_artist
            if let Some(bracket_pos) = dir_name.rfind('[') {
                let dir_name_without_artist = &dir_name[..bracket_pos - 1];
                if dir_name_without_artist.is_empty() {
                    continue;
                }

                // Check folder
                let dir_path_without_artist = root_dir.join(dir_name_without_artist);
                if !dir_path_without_artist.is_dir() {
                    continue;
                }

                // Check has another folders
                let dir_names_with_starter: Vec<_> = dir_names
                    .iter()
                    .filter(|name| name.starts_with(&format!("{dir_name_without_artist} [")))
                    .collect();

                if dir_names_with_starter.len() > 2 {
                    println!(
                        " !_! {} have more then 2 folders! {:?}",
                        dir_name_without_artist, dir_names_with_starter
                    );
                    continue;
                }

                // Append
                pairs.push((dir_name.clone(), dir_name_without_artist.to_string()));
            }
        }
    }

    // Check duplicate
    let mut last_from_dir_name = String::new();
    let mut duplicate_list = Vec::new();
    for (_, from_dir_name) in &pairs {
        if last_from_dir_name == *from_dir_name {
            duplicate_list.push(from_dir_name.clone());
        }
        last_from_dir_name = from_dir_name.clone();
    }

    if !duplicate_list.is_empty() {
        println!("Duplicate!");
        for name in &duplicate_list {
            println!(" -> {}", name);
        }
        return Err(io::Error::other("Duplicate folders found"));
    }

    // Confirm
    for (target_dir_name, from_dir_name) in &pairs {
        println!("- Find Dir pair: {} <- {}", target_dir_name, from_dir_name);
    }

    println!("There are {} actions. Do transferring? [y/N]:", pairs.len());
    let mut input = String::new();
    std::io::stdin().read_line(&mut input)?;

    if !input.trim().to_lowercase().starts_with('y') {
        println!("Aborted.");
        return Ok(());
    }

    for (target_dir_name, from_dir_name) in pairs {
        let from_dir_path = root_dir.join(&from_dir_name);
        let target_dir_path = root_dir.join(&target_dir_name);
        println!(" - Moving: {} <- {}", target_dir_name, from_dir_name);
        move_elements_across_dir(
            &from_dir_path,
            &target_dir_path,
            Default::default(),
            replace_options_update_pack(),
        )
        .await?;
    }

    Ok(())
}

/// Move works from directory A to directory B (auto merge)
pub async fn move_works_in_pack(
    root_dir_from: impl AsRef<Path>,
    root_dir_to: impl AsRef<Path>,
) -> io::Result<()> {
    let root_dir_from = root_dir_from.as_ref();
    let root_dir_to = root_dir_to.as_ref();

    if root_dir_from == root_dir_to {
        return Ok(());
    }

    let mut move_count = 0;
    let mut entries = fs::read_dir(root_dir_from).await?;

    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let bms_dir = entry.path();
        if !bms_dir.is_dir() {
            continue;
        }

        let bms_dir_name = bms_dir
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");
        println!("Moving: {}", bms_dir_name);

        let dst_bms_dir = root_dir_to.join(bms_dir_name);
        move_elements_across_dir(
            &bms_dir,
            &dst_bms_dir,
            Default::default(),
            replace_options_update_pack(),
        )
        .await?;
        move_count += 1;
    }

    if move_count > 0 {
        println!("Move {} songs.", move_count);
        return Ok(());
    }

    // Deal with song dir
    move_elements_across_dir(
        root_dir_from,
        root_dir_to,
        Default::default(),
        replace_options_update_pack(),
    )
    .await?;

    Ok(())
}

/// Move out one level directory (auto merge)
pub async fn move_out_works(target_root_dir: impl AsRef<Path>) -> io::Result<()> {
    let target_root_dir = target_root_dir.as_ref();
    let mut entries = fs::read_dir(target_root_dir).await?;

    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let root_dir_path = entry.path();
        if !root_dir_path.is_dir() {
            continue;
        }

        let mut sub_entries = fs::read_dir(&root_dir_path).await?;
        while let Some(sub_entry) = sub_entries.next().await {
            let sub_entry = sub_entry?;
            let work_dir_path = sub_entry.path();
            if !work_dir_path.is_dir() {
                continue;
            }

            let work_dir_name = work_dir_path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown");
            let target_work_dir_path = target_root_dir.join(work_dir_name);

            // Deal with song dir
            move_elements_across_dir(
                &work_dir_path,
                &target_work_dir_path,
                Default::default(),
                replace_options_update_pack(),
            )
            .await?;
        }

        // Check if directory is empty and remove it
        let mut check_entries = fs::read_dir(&root_dir_path).await?;
        if check_entries.next().await.is_none() {
            fs::remove_dir(&root_dir_path).await?;
        }
    }

    Ok(())
}

/// Remove unnecessary media files
async fn workdir_remove_unneed_media_files(
    work_dir: &Path,
    rule: &[(Vec<String>, Vec<String>)],
) -> io::Result<()> {
    let mut remove_pairs = Vec::new();
    let mut removed_files = HashSet::new();

    let mut entries = fs::read_dir(work_dir).await?;
    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let file_path = entry.path();
        if !file_path.is_file() {
            continue;
        }

        let file_name = file_path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        let file_ext = file_name.rsplit('.').next().unwrap_or("").to_lowercase();

        for (upper_exts, lower_exts) in rule {
            if !upper_exts.contains(&file_ext) {
                continue;
            }

            // File is empty?
            let metadata = fs::metadata(&file_path).await?;
            if metadata.len() == 0 {
                println!(" - !x!: File {} is Empty! Skipping...", file_path.display());
                continue;
            }

            // File is in upper_exts, search for file in lower_exts.
            for lower_ext in lower_exts {
                let replacing_file_path = file_path.with_extension(lower_ext);

                // File not exist?
                if !replacing_file_path.exists() {
                    continue;
                }
                if removed_files.contains(&replacing_file_path) {
                    continue;
                }
                remove_pairs.push((file_path.clone(), replacing_file_path.clone()));
                removed_files.insert(replacing_file_path);
            }
        }
    }

    if !remove_pairs.is_empty() {
        println!("Entering: {}", work_dir.display());
    }

    // Remove file
    for (file_path, replacing_file_path) in remove_pairs {
        println!(
            "- Remove file {}, because {} exists.",
            replacing_file_path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy(),
            file_path.file_name().unwrap_or_default().to_string_lossy()
        );
        fs::remove_file(&replacing_file_path).await?;
    }

    // Finished: Count Ext
    let mut ext_count: HashMap<String, Vec<String>> = HashMap::new();
    let mut count_entries = fs::read_dir(work_dir).await?;
    while let Some(entry) = count_entries.next().await {
        let entry = entry?;
        let file_path = entry.path();
        if !file_path.is_file() {
            continue;
        }

        // Count ext
        let file_name = file_path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        let file_ext = file_name.rsplit('.').next().unwrap_or("").to_lowercase();

        ext_count
            .entry(file_ext)
            .or_default()
            .push(file_name.to_string());
    }

    // Do With Ext Count
    if let Some(mp4_count) = ext_count.get("mp4")
        && mp4_count.len() > 1
    {
        println!(
            " - Tips: {} has more than 1 mp4 files! {:?}",
            work_dir.display(),
            mp4_count
        );
    }

    Ok(())
}

pub fn get_remove_media_rule_oraja() -> Vec<(Vec<String>, Vec<String>)> {
    vec![
        (
            vec!["mp4".to_string()],
            vec![
                "avi".to_string(),
                "wmv".to_string(),
                "mpg".to_string(),
                "mpeg".to_string(),
            ],
        ),
        (
            vec!["avi".to_string()],
            vec!["wmv".to_string(), "mpg".to_string(), "mpeg".to_string()],
        ),
        (
            vec!["flac".to_string(), "wav".to_string()],
            vec!["ogg".to_string()],
        ),
        (vec!["flac".to_string()], vec!["wav".to_string()]),
        (vec!["mpg".to_string()], vec!["wmv".to_string()]),
    ]
}

pub fn get_remove_media_rule_wav_fill_flac() -> Vec<(Vec<String>, Vec<String>)> {
    vec![(vec!["wav".to_string()], vec!["flac".to_string()])]
}

pub fn get_remove_media_rule_mpg_fill_wmv() -> Vec<(Vec<String>, Vec<String>)> {
    vec![(vec!["mpg".to_string()], vec!["wmv".to_string()])]
}

pub fn get_remove_media_file_rules() -> Vec<Vec<(Vec<String>, Vec<String>)>> {
    vec![
        get_remove_media_rule_oraja(),
        get_remove_media_rule_wav_fill_flac(),
        get_remove_media_rule_mpg_fill_wmv(),
    ]
}

/// Remove unnecessary media files
pub async fn remove_unneed_media_files(
    root_dir: impl AsRef<Path>,
    rule: Option<Vec<(Vec<String>, Vec<String>)>>,
) -> io::Result<()> {
    let root_dir = root_dir.as_ref();
    let rule = match rule {
        Some(r) => r,
        None => {
            // Select Preset
            let rules = get_remove_media_file_rules();
            for (i, rule) in rules.iter().enumerate() {
                println!("- {}: {:?}", i, rule);
            }
            println!("Select Preset (Default: 0):");
            let mut input = String::new();
            std::io::stdin().read_line(&mut input)?;
            let selection: usize = input.trim().parse().unwrap_or(0);
            rules.get(selection).unwrap_or(&rules[0]).clone()
        }
    };

    println!("Selected: {:?}", rule);

    // Do
    let mut entries = fs::read_dir(root_dir).await?;
    while let Some(entry) = entries.next().await {
        let entry = entry?;
        let bms_dir_path = entry.path();
        if !bms_dir_path.is_dir() {
            continue;
        }

        workdir_remove_unneed_media_files(&bms_dir_path, &rule).await?;
    }

    Ok(())
}

/// Merge subfolders with similar names from source folder (dir_from) to corresponding subfolders in target folder (dir_to)
pub async fn move_works_with_same_name(
    root_dir_from: impl AsRef<Path>,
    root_dir_to: impl AsRef<Path>,
) -> io::Result<()> {
    let root_dir_from = root_dir_from.as_ref();
    let root_dir_to = root_dir_to.as_ref();

    // Verify input paths exist and are directories
    if !root_dir_from.is_dir() {
        return Err(io::Error::other(format!(
            "Source path does not exist or is not a directory: {}",
            root_dir_from.display()
        )));
    }
    if !root_dir_to.is_dir() {
        return Err(io::Error::other(format!(
            "Target path does not exist or is not a directory: {}",
            root_dir_to.display()
        )));
    }

    // Get all direct subfolders in source directory
    let mut from_subdirs = Vec::new();
    let mut from_entries = fs::read_dir(root_dir_from).await?;
    while let Some(entry) = from_entries.next().await {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir()
            && let Some(name) = path.file_name().and_then(|n| n.to_str())
        {
            from_subdirs.push(name.to_string());
        }
    }

    // Get all direct subfolders in target directory
    let mut to_subdirs = Vec::new();
    let mut to_entries = fs::read_dir(root_dir_to).await?;
    while let Some(entry) = to_entries.next().await {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir()
            && let Some(name) = path.file_name().and_then(|n| n.to_str())
        {
            to_subdirs.push(name.to_string());
        }
    }

    let mut pairs = Vec::new();

    // Iterate through each subfolder in source directory
    for from_dir_name in &from_subdirs {
        let from_dir_path = root_dir_from.join(from_dir_name);

        // Find matching target subfolder (name contains source folder name)
        for to_dir_name in &to_subdirs {
            if to_dir_name.contains(from_dir_name) {
                let to_dir_path = root_dir_to.join(to_dir_name);
                pairs.push((
                    from_dir_name.clone(),
                    from_dir_path.clone(),
                    to_dir_name.clone(),
                    to_dir_path,
                ));
                break;
            }
        }
    }

    for (from_dir_name, _, to_dir_name, _) in &pairs {
        println!(" -> {} => {}", from_dir_name, to_dir_name);
    }

    println!("Merge? [y/N]");
    let mut input = String::new();
    std::io::stdin().read_line(&mut input)?;

    if !input.trim().to_lowercase().starts_with('y') {
        println!("Operation cancelled");
        return Ok(());
    }

    // Merge source folder contents to each matching target folder
    for (_, from_dir_path, _, target_path) in pairs {
        println!(
            "Merge: '{}' -> '{}'",
            from_dir_path.display(),
            target_path.display()
        );
        move_elements_across_dir(
            &from_dir_path,
            &target_path,
            Default::default(),
            replace_options_update_pack(),
        )
        .await?;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_first_char_rules_find() {
        assert_eq!(first_char_rules_find("123abc"), "0-9");
        assert_eq!(first_char_rules_find("ABC"), "ABCD");
        assert_eq!(first_char_rules_find("EFG"), "EFGHIJK");
        assert_eq!(first_char_rules_find("LMN"), "LMNOPQ");
        assert_eq!(first_char_rules_find("RST"), "RST");
        assert_eq!(first_char_rules_find("UVW"), "UVWXYZ");
        assert_eq!(first_char_rules_find("あいう"), "平假");
        assert_eq!(first_char_rules_find("アイウ"), "片假");
        assert_eq!(first_char_rules_find("中文"), "字");
        assert_eq!(first_char_rules_find(""), "Uncategorized");
    }

    #[test]
    fn test_get_remove_media_rules() {
        let oraja = get_remove_media_rule_oraja();
        assert_eq!(oraja.len(), 5);

        let wav_fill_flac = get_remove_media_rule_wav_fill_flac();
        assert_eq!(wav_fill_flac.len(), 1);

        let mpg_fill_wmv = get_remove_media_rule_mpg_fill_wmv();
        assert_eq!(mpg_fill_wmv.len(), 1);

        let all_rules = get_remove_media_file_rules();
        assert_eq!(all_rules.len(), 3);
    }
}
