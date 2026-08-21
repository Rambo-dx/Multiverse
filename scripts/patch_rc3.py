from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
p = root / 'index.html'
s = p.read_text(encoding='utf-8')

# RC2 prerequisite hotfix: manual Tags/Traits must participate in Power prerequisites.
s = s.replace(
    'const tags = new Set(); const traits = new Set(d.extra_traits||[]);',
    'const tags = new Set([...(d.tags||[]), ...(d.extra_tags||[])]); const traits = new Set([...(d.traits||[]), ...(d.extra_traits||[])]);',
    1,
)

# RC3 version.
s = s.replace('const APP_VERSION = "v1.80 RC1";', 'const APP_VERSION = "v1.80 RC3";', 1)
s = s.replace('const APP_VERSION = "v1.80 RC2";', 'const APP_VERSION = "v1.80 RC3";', 1)

helper = '''/* Recovery amount (RC3): errata-corrected and shared by every Recovery entry point.\n   Health = (Marvel die × effective Rank) + effective Resilience.\n   Focus  = (Marvel die × effective Rank) + effective Vigilance.\n   Fantastic success doubles the entire result. */\nfunction computeRecoveryAmount(roll, effectiveRank, effectiveAbility){\n  let amount = (Number(roll.marvelDie)||0) * (Number(effectiveRank)||0) + (Number(effectiveAbility)||0);\n  if(roll.fantastic) amount *= 2;\n  return amount;\n}\n\n'''
marker = '/* Recovery Check (P2, V1.41): el jugador la dispara desde su ficha gastando 1 Karma -- abre la\n'
if 'function computeRecoveryAmount(' not in s:
    if marker not in s:
        raise RuntimeError('Recovery marker not found')
    s = s.replace(marker, helper + marker, 1)

start = s.index('async function startRecoveryCheck(ch, target){')
end_marker = '\n}\n\n\n\n/* Daño real'
end = s.index(end_marker, start) + 2
new_first = '''async function startRecoveryCheck(ch, target){\n  if(ch.cur_karma<=0) return;\n  ch.cur_karma -= 1;\n  const eff = getEffectiveCharacter(ch);\n  const ability = target==="focus" ? "vigilance" : "resilience";\n  const abilityScore = Number(eff.abilities?.[ability] ?? 0);\n  const roll = resolveActionCheck({abilityScore, tn:10, edges:[], troubles:[]});\n  const d = computeDerived(eff);\n  let note;\n  if(roll.success){\n    const gain = computeRecoveryAmount(roll, eff.rank, abilityScore);\n    if(target==="focus"){\n      const before = ch.cur_focus;\n      ch.cur_focus = Math.min(d.focus, ch.cur_focus + gain);\n      note = `Recuperaste ${ch.cur_focus-before} de Focus (${ch.cur_focus}/${d.focus}).`;\n    } else {\n      const before = ch.cur_health;\n      ch.cur_health = Math.min(d.health, ch.cur_health + gain);\n      note = `Recuperaste ${ch.cur_health-before} de Salud (${ch.cur_health}/${d.health}).`;\n    }\n  } else {\n    note = "El check falló — no recuperas nada, pero ya gastaste el punto de Karma.";\n  }\n  await save("character", ch);\n  await showRawModal(`${diceHTML(roll)}<p class="small" style="margin-top:8px">${esc(note)}</p>`, "Entendido");\n  renderAll();\n}'''
s = s[:start] + new_first + s[end:]

old_override = """window.startRecoveryCheck=async function(ch,target){if(ch.cur_karma<=0)return;const ability=target==='focus'?'vigilance':'resilience';ch.cur_karma-=1;const roll=actionRoll(ch,ability,10);const d=computeDerived(getEffectiveCharacter(ch));let note;if(roll.success){let gain=roll.marvelDie*ch.rank;if(roll.fantastic)gain*=2;if(target==='focus'){const before=ch.cur_focus;ch.cur_focus=Math.min(d.focus,ch.cur_focus+gain);note=`Recuperaste ${ch.cur_focus-before} de Focus (${ch.cur_focus}/${d.focus}).`;}else{const before=ch.cur_health;ch.cur_health=Math.min(d.health,ch.cur_health+gain);note=`Recuperaste ${ch.cur_health-before} de Salud (${ch.cur_health}/${d.health}).`;if(ch.cur_health>before){const idx=(ch.active_conditions||[]).findIndex(c=>(c.name||c)==='Bleeding');if(idx>=0){ch.active_conditions.splice(idx,1);note+=' Bleeding terminó.';}}}}else note='El check falló — no recuperas nada, pero el Karma ya se gastó.';if(window.v173Log)window.v173Log(ch,'recovery',`Recovery ${target}`,note);await save('character',ch);await showRawModal(`${diceHTML(roll)}<p class="small">${esc(note)}</p>`,'Entendido');renderAll();};"""
new_override = """window.startRecoveryCheck=async function(ch,target){\n    if(ch.cur_karma<=0)return;\n    const ability=target==='focus'?'vigilance':'resilience';\n    ch.cur_karma-=1;\n    const eff=getEffectiveCharacter(ch);\n    const roll=actionRoll(ch,ability,10);\n    const d=computeDerived(eff);\n    const effectiveAbility=Number(eff.abilities?.[ability]??0);\n    let note;\n    if(roll.success){\n      const gain=computeRecoveryAmount(roll,eff.rank,effectiveAbility);\n      if(target==='focus'){\n        const before=ch.cur_focus;\n        ch.cur_focus=Math.min(d.focus,ch.cur_focus+gain);\n        note=`Recuperaste ${ch.cur_focus-before} de Focus (${ch.cur_focus}/${d.focus}).`;\n      }else{\n        const before=ch.cur_health;\n        ch.cur_health=Math.min(d.health,ch.cur_health+gain);\n        note=`Recuperaste ${ch.cur_health-before} de Salud (${ch.cur_health}/${d.health}).`;\n        if(ch.cur_health>before){\n          const idx=(ch.active_conditions||[]).findIndex(c=>(c.name||c)==='Bleeding');\n          if(idx>=0){ch.active_conditions.splice(idx,1);note+=' Bleeding terminó.';}\n        }\n      }\n    }else note='El check falló — no recuperas nada, pero el Karma ya se gastó.';\n    if(window.v173Log)window.v173Log(ch,'recovery',`Recovery ${target}`,note);\n    await save('character',ch);\n    await showRawModal(`${diceHTML(roll)}<p class="small">${esc(note)}</p>`,'Entendido');\n    renderAll();\n  };"""
if old_override not in s:
    raise RuntimeError('Living Combat Recovery override not found')
s = s.replace(old_override, new_override, 1)

if 'let gain=roll.marvelDie*ch.rank' in s:
    raise RuntimeError('Old Recovery regression still present')

p.write_text(s, encoding='utf-8')

sw = root / 'sw.js'
if sw.exists():
    t = sw.read_text(encoding='utf-8')
    t = t.replace('multiverse-v1.80-rc1', 'multiverse-v1.80-rc3')
    t = t.replace('multiverse-v1.80-rc2', 'multiverse-v1.80-rc3')
    sw.write_text(t, encoding='utf-8')
