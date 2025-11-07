from dataclasses import dataclass
from . import envmanager


@dataclass(frozen=True, slots=True)
class AutoLoaderOption:
    key: str
    value: str
    hidden: bool = False

    def __iter__(self):
        yield (self.key, self)


class AutoLoaderFormat:
    def __init__(self):
        self.name = None
        self.options: set[AutoLoaderOption] = {
            AutoLoaderOption("cloudFiles.inferColumnTypes", "true", True),
            AutoLoaderOption("cloudFiles.schemaEvolutionMode", "addNewColumns"),
            AutoLoaderOption("cloudFiles.cleanSource", "MOVE", True),
            AutoLoaderOption("cloudFiles.cleanSource.retentionDuration", "1 day", True),
            AutoLoaderOption(
                "cloudFiles.cleanSource.moveDestination",
                f"{envmanager.get_config()['volume_path_archive']}/{{table_name}}",
                True,
            ),
        }
        self.expectations: dict[str, str] = {
            "Rescued data should be null": "_rescued_data IS NULL"
        }
        self.default_schema: set[str] = {"_rescued_data STRING"}

    def get_default_schema(self) -> str:
        return ", ".join(self.default_schema)

    def get_userfacing_options(self) -> dict[str, str]:
        return {opt.key: opt.value for opt in self.options if not opt.hidden}

    def validate_user_options(self, options: dict[str, str]) -> None:
        allowed = set(self.get_userfacing_options())
        illegal = set(options) - allowed
        if illegal:
            raise ValueError(
                f"Unsupported or protected options: {sorted(illegal)}. "
                f"Allowed user options: {sorted(allowed)}"
            )

    def get_modified_options(self, options: dict[str, str]) -> dict[str, str]:
        self.validate_user_options(options)
        defaults = self.get_userfacing_options()
        return {k: v for k, v in options.items() if k in defaults and v != defaults[k]}

    def get_merged_options(
        self, options: dict[str, str], table_name: str, is_placeholder: bool = False
    ) -> dict[str, str]:
        self.validate_user_options(options)
        defaults = {opt.key: opt.value for opt in self.options}

        merged = defaults.copy()
        merged.update({k: v for k, v in options.items() if k in defaults})

        # Do not specify schema evolution mode in placeholder
        if is_placeholder:
            merged.pop("cloudFiles.schemaEvolutionMode", None)

        # Format the moveDestination with table_name
        move_dest_key = "cloudFiles.cleanSource.moveDestination"
        if move_dest_key in merged:
            merged[move_dest_key] = merged[move_dest_key].format(table_name=table_name)

        return merged


class CSV(AutoLoaderFormat):
    def __init__(self):
        super().__init__()
        self.name = "CSV"
        self.options |= {
            AutoLoaderOption("header", "true"),
            AutoLoaderOption("mergeSchema", "true", True),
            AutoLoaderOption("mode", "PERMISSIVE", True),
            AutoLoaderOption("columnNameOfCorruptRecord", "_corrupt_record", True),
            AutoLoaderOption("delimiter", ","),
            AutoLoaderOption("escape", '"'),
            AutoLoaderOption("multiLine", "false"),
        }
        self.expectations |= {
            "Corrupted record should be null": "_corrupt_record IS NULL"
        }
        self.default_schema |= {"_corrupt_record STRING"}


class JSON(AutoLoaderFormat):
    def __init__(self):
        super().__init__()
        self.name = "JSON"
        self.options |= {
            AutoLoaderOption("mergeSchema", "true", True),
            AutoLoaderOption("mode", "PERMISSIVE", True),
            AutoLoaderOption("columnNameOfCorruptRecord", "_corrupt_record", True),
            AutoLoaderOption("allowComments", "true"),
            AutoLoaderOption("allowSingleQuotes", "true"),
            AutoLoaderOption("inferTimestamp", "true"),
            AutoLoaderOption("multiLine", "true"),
        }
        self.expectations |= {
            "Corrupted record should be null": "_corrupt_record IS NULL"
        }
        self.default_schema |= {"_corrupt_record STRING"}


class AVRO(AutoLoaderFormat):
    def __init__(self):
        super().__init__()
        self.name = "AVRO"
        self.options |= {
            AutoLoaderOption("mergeSchema", "true", True),
        }


class PARQUET(AutoLoaderFormat):
    def __init__(self):
        super().__init__()
        self.name = "PARQUET"
        self.options |= {
            AutoLoaderOption("mergeSchema", "true", True),
        }


# Cache the supported formats so they are only created on the first call
_supported_formats_cache = {}

def get_supported_formats() -> dict[str, AutoLoaderFormat]:
    if not _supported_formats_cache:
        _supported_formats_cache.update({
            f.name: f for f in (CSV(), JSON(), AVRO(), PARQUET())
        })
    return _supported_formats_cache


def get_format_manager(fmt: str) -> dict[str, str]:
    key = fmt.strip().upper()
    try:
        return get_supported_formats()[key]
    except KeyError:
        supported = ", ".join(sorted(get_supported_formats().keys()))
        raise ValueError(
            f"{fmt!r} is not a supported format. Supported formats: {supported}"
        )
