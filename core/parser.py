import re


def extract_instructions(content: str, log) -> list:
    instructions = []
    lines        = content.split("\n")
    i            = 0

    while i < len(lines):
        stripped = lines[i].strip()

        m = re.match(r'^ETIQUETA\[([^\]]+)\]\s*$', stripped)
        if not m:
            i += 1
            continue

        params_str = m.group(1)
        params     = [p.strip() for p in params_str.split(",")]

        if len(params) != 4:
            log(f"  WARN: ETIQUETA inválida ({len(params)} params): [{params_str}]", "warn")
            i += 1
            continue

        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s == "" or re.match(r'^`{3,}\w*\s*$', s):
                j += 1
                continue
            break

        if j >= len(lines) or lines[j].strip() != "INICIO_BLOQUE":
            log(f"  WARN: sin INICIO_BLOQUE → [{params_str}]", "warn")
            i += 1
            continue

        k          = j + 1
        code_lines = []
        found      = False

        while k < len(lines):
            if lines[k].rstrip() == "FIN_BLOQUE":
                found = True
                break
            code_lines.append(lines[k])
            k += 1

        if not found:
            log(f"  WARN: FIN_BLOQUE no encontrado → [{params_str}]", "warn")
            i += 1
            continue

        final = [cl for cl in code_lines
                 if not re.match(r'^\s*`{3,}\w*\s*$', cl)]
        code  = "\n".join(final).strip()

        ubicacion, nombre, extension, accion = params
        accion = accion.upper().strip()

        if accion == "EJECUTAR" or nombre.lower() == "nan":
            filepath = "CMD"
        elif nombre == "":
            filepath = f".{extension}" if ubicacion == "." else f"{ubicacion}/.{extension}"
        elif ubicacion == ".":
            filepath = f"{nombre}.{extension}"
        else:
            filepath = f"{ubicacion}/{nombre}.{extension}"

        instructions.append({
            "ubicacion": ubicacion, "nombre":   nombre,
            "extension": extension, "action":   accion,
            "language":  "",        "content":  code,
            "filepath":  filepath,
        })

        i = k + 1

    return instructions
