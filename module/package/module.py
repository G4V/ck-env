#
# Collective Knowledge (package)
#
# See CK LICENSE.txt for licensing details
# See CK Copyright.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://cTuning.org/lab/people/gfursin
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings
env_install_path='CK_TOOLS'

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# install package

def install(i):
    """
    Input:  {
              (host_os)           - host OS (detect, if omitted)
              (target_os)         - target OS (detect, if omitted)
              (target_device_id)  - target device ID (detect, if omitted)

              (data_uoa) or (uoa) - package UOA entry

              (env_data_uoa)      - use this data UOA to record (new) env
              (env_repo_uoa)      - use this repo to record new env

              (install_path)      - path with soft is installed

              (skip_process)      - if 'yes', skip archive processing
              (skip_setup)        - if 'yes', skip environment setup
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    import os

    o=i.get('out','')

    import time
    start_time = time.time()

    # Check package description
    duoa=i.get('uoa','')
    duid=''
    dname=''
    d={}

    if duoa=='':
       # Try to detect CID in current path
       rx=ck.detect_cid_in_current_path({})
       if rx['return']==0:
          duoa=rx.get('data_uoa','')

    if duoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':work['self_module_uid'],
                     'data_uoa':duoa})
       if rx['return']>0: return rx
       d=rx['dict']
       p=rx['path']

       duoa=rx['data_uoa']
       duid=rx['data_uid']
    else:
       # Attempt to load configuration from the current directory
       p=os.getcwd()
       pc=os.path.join(p, ck.cfg['subdir_ck_ext'], ck.cfg['file_meta'])

       found=False
       if os.path.isfile(pc):
          r=ck.load_json_file({'json_file':pc})
          if r['return']==0:
             d=r['dict']
             found=True

       if not found:
          return {'return':1, 'error':'package UOA (data_uoa) is not defined'}

    # Get main params
    tags=d.get('tags',[])
    cus=d.get('customize',{})
    env=d.get('env',{})

    udeps=d.get('deps',{})

    suoa=d.get('soft_uoa','')

    dname=d.get('package_name','')

    ver=cus.get('version','')
    extra_dir=cus.get('extra_dir','')

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('target_device_id','')

    if tos=='': tos=d.get('default_target_os_uoa','')

    r=ck.access({'action':'detect',
                 'module_uoa':cfg['module_deps']['platform.os'],
                 'host_os':hos,
                 'target_os':tos,
                 'target_device_id':tdid,
                 'skip_info_collection':'yes'})
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    tbits=tosd.get('bits','')

    tags.append('host-os-'+hosx)
    tags.append('target-os-'+tosx)
    tags.append(tbits+'bits')

    rem=hosd.get('rem','')
    eset=hosd.get('env_set','')
    svarb=hosd.get('env_var_start','')
    svare=hosd.get('env_var_stop','')
    scall=hosd.get('env_call','')
    sdirs=hosd.get('dir_sep','')
    sext=hosd.get('script_ext','')
    evs=hosd.get('env_var_separator','')
    eifs=hosd.get('env_quotes_if_space','')
    eifsc=hosd.get('env_quotes_if_space_in_call','')
    wb=tosd.get('windows_base','')

    enruoa=i.get('env_repo_uoa','')
    enduoa=i.get('env_data_uoa','')

    # Search by exact terms
    setup={'host_os_uoa':hos,
           'target_os_uoa':tos,
           'target_os_bits':tbits}
    if ver!='':
       setup['version']=ver

    # Resolve deps
    if cus.get('ignore_deps','')=='yes':
       udeps={}

    sdeps=''
    if len(udeps)>0:
       ii={'action':'resolve',
           'module_uoa':cfg['module_deps']['env'],
           'host_os':hos,
           'target_os':tos,
           'target_device_id':tdid,
           'repo_uoa':enruoa,
           'deps':udeps}
       if o=='con': ii['out']='con'

       rx=ck.access(ii)
       if rx['return']>0: return rx
       sdeps=rx['bat']
       udeps=rx['deps'] # Update deps (add UOA)

    for q in udeps:
        v=udeps[q]
        setup['deps_'+q]=v['uoa']

    # Convert tags to string
    stags=''
    for q in tags:
        if q!='':
           if stags!='': stags+=','
           stags+=q.strip()

    # Check installation path
    pi=i.get('install_path','')

    x=cus.get('input_path_example','')
    if x!='': pie=' (example: '+ye+')'
    else: pie=''

    xprocess=True
    xsetup=True

    if i.get('skip_process','')=='yes': xprocess=False
    if i.get('skip_setup','')=='yes': xsetup=False

    ps=d.get('process_script','')

    if pi=='':
       # Check if environment already exists to check installation path
       if enduoa=='':
          if o=='con':
             ck.out('')
             ck.out('Searching if environment already exists using:')
             ck.out('  * Tags: '+stags)
             if len(udeps)>0:
                for q in udeps:
                    v=udeps[q]
                    ck.out('  * Dependency: '+q+'='+v.get('uoa',''))

          r=ck.access({'action':'search',
                       'module_uoa':cfg['module_deps']['env'],
                       'tags':stags,
                       'search_dict':{'setup':setup}})
          if r['return']>0: return r
          lst=r['lst']
          if len(lst)>0:
             fe=lst[0]

             enduoa=fe['data_uoa']
             enduid=fe['data_uid']

             if o=='con':
                x=enduoa
                if enduid!=enduoa: x+=' ('+enduid+')'

                ck.out('')
                ck.out('Environment found: '+x)
          else:
             if o=='con':
                ck.out('')
                ck.out('Environment not found ...')

       # Load env if exists
       if enduoa!='':
          r=ck.access({'action':'load',
                       'module_uoa':cfg['module_deps']['env'],
                       'repo_uoa':enruoa,
                       'data_uoa':enduoa})
          if r['return']>0: return r
          de=r['dict']
          pi=de.get('customize',{}).get('path_install','')

          if extra_dir!='':
             j=pi.rfind(extra_dir)
             if j>=0:
                pi=pi[:j]

             if pi!='':
                j=len(pi)
                if pi[j-1]==sdirs:
                   pi=pi[:-1]

          if pi!='':
             if o=='con':
                if xprocess:
                   ck.out('')
                   ck.out('Package is already installed in path: '+pi)

                   if ps!='':
                      ck.out('')
                      rx=ck.inp({'text':'Would you like to overwrite/process it again (y/N)? '})
                      x=rx['string'].strip().lower()
                      if x!='y' and x!='yes':
                         xprocess=False

                if xsetup:
                   ck.out('')
                   rx=ck.inp({'text':'Would you like to setup environment for this package again (Y/n)? '})
                   x=rx['string'].strip().lower()
                   if x=='n' or x=='no':
                      xsetup=False

             else:
                return {'return':1, 'error':'package is already installed in path '+pi}

       if pi=='' and cus.get('skip_path','')!='yes':
          if o=='con':
             ck.out('')

             pix=''
             sp=d.get('suggested_path','')

             if os.environ.get(env_install_path,'')!='' and sp!='':
                x=os.environ[env_install_path]

                nm=sp+'-'+cus.get('version','')

                bdn=udeps.get('compiler',{}).get('build_dir_name','')
                if bdn!='':
                   nm+='-'+bdn
                   vr=udeps.get('compiler',{}).get('ver','')
                   if vr!='':
                      nm+='-'+vr

                nm+='-'+tosx

                pix=os.path.join(x, nm)
                if not tosx.endswith(tbits): pix+='-'+tbits
                ck.out('Suggested path: '+pix)

                r=ck.inp({'text':'  Press Enter to use suggested path or input new installation path '+pie+': '})
                pi=r['string'].strip()
                if pi=='': pi=pix
             else:
                r=ck.inp({'text':'Enter installation path '+pie+': '})
                pi=r['string'].strip()

       if pi=='' and cus.get('skip_path','')!='yes':
          return {'return':1, 'error':'installation path is not specified'}

    # Check dependencies
    deps={}
    if suoa!='':
       rx=ck.access({'action':'load',
                     'module_uoa':cfg['module_deps']['soft'],
                     'data_uoa':suoa})
       if rx['return']>0: return rx
       dx=rx['dict']
       deps=dx.get('deps',{})

    # Update by package deps (more precise)
    for q in deps:
        v=deps[q]
        if q not in udeps:
           udeps[q]=v

    # Prepare environment based on deps
    if cus.get('ignore_deps','')=='yes':
       udeps={}

    sdeps=''
    if len(udeps)>0:
       ii={'action':'resolve',
           'module_uoa':cfg['module_deps']['env'],
           'host_os':hos,
           'target_os':tos,
           'target_device_id':tdid,
           'repo_uoa':enruoa,
           'deps':udeps}
       if o=='con': ii['out']='con'

       rx=ck.access(ii)
       if rx['return']>0: return rx
       sdeps=rx['bat']

    # Check if continue processing
    if ps!='' and xprocess:
       # start bat
       sb=hosd.get('batch_prefix','')+'\n'

       # Check installation path
       if pi=='' and cus.get('skip_path','')!='yes':
          if o=='con':
             ck.out('')

             pix=''
             sp=d.get('suggested_path','')
             if os.environ.get(env_install_path,'')!='' and sp!='':
                x=os.environ[env_install_path]
                pix=os.path.join(x, sp+'-'+cus.get('version','')+'-'+tosx)
                if not tosx.endswith(tbits): pix+='-'+tbits
                ck.out('Suggested path: '+pix)
                r=ck.inp({'text':'  Press Enter to use suggested path or input new installation path '+pie+': '})
                pi=r['string'].strip()
                if pi=='': pi=pix
             else:
                r=ck.inp({'text':'Enter installation path '+pie+': '})
                pi=r['string'].strip()

          if pi=='':
             return {'return':1, 'error':'installation path is not specified'}

       # Prepare process script
       ps+=sext
       px=os.path.join(p,ps)

       if not os.path.isfile(px):
          return {'return':1, 'error':'processing script '+ps+' is not found'}

       # Add deps if needed before running
       if sdeps!='':
          sb+=sdeps

       # If install path has space, add quotes for some OS ...
       xs=''
       if pi.find(' ')>=0 and eifs!='': xs=eifs
       sb+=eset+' INSTALL_DIR='+xs+pi+xs+'\n'

       xs=''
       if p.find(' ')>=0 and eifs!='': xs=eifs
       sb+=eset+' PACKAGE_DIR='+xs+p+xs+'\n'

       sb+='\n'

       xs=''
       if p.find(' ')>=0 and eifsc!='': xs=eifsc
       sb+=scall+' '+xs+px+xs+'\n\n'

       if wb=='yes': sb+='exit /b 0\n'

       # Generate tmp file
       rx=ck.gen_tmp_file({'prefix':'tmp-ck-', 'suffix':sext})
       if rx['return']>0: return rx
       fn=rx['file_name']

       # Write to tmp file
       rx=ck.save_text_file({'text_file':fn, 'string':sb})
       if rx['return']>0: return rx

       # Go to installation path
       if not os.path.isdir(pi):
          os.makedirs(pi)
       os.chdir(pi)

       # Check if need to set executable flags
       se=hosd.get('set_executable','')
       if se!='':
          x=se+' '+fn
          rx=os.system(x)

       # Run script
       rx=os.system(fn)
       if os.path.isfile(fn): os.remove(fn)

       if rx>0: 
          return {'return':1, 'error':'processing archive failed'}

    # Check if need to setup environment
    if xsetup:
       if suoa=='':
          return {'return':1, 'error':'Software environment UOA is not defined in this package (soft_uoa)'}

       if extra_dir!='':
          pi+=sdirs+extra_dir

       if suoa!='':
          if o=='con':
             ck.out('')
             ck.out('Setting up environment for installed package ...')
             ck.out('')

          nw='no'
          if enduoa=='': nw='yes'

          ii={'action':'setup',
              'module_uoa':cfg['module_deps']['soft'],
              'data_uoa':suoa,
              'soft_name':dname,
              'host_os':hos,
              'target_os':tos,
              'target_device_id':tdid,
              'tags':stags,
              'customize':cus,
              'env_new':'yes',
              'env_repo_uoa':enruoa,
              'env_data_uoa':enduoa,
              'env':env,
              'deps':udeps,
              'install_path':pi
             }
          if duid!='': ii['package_uoa']=duid
          if o=='con': ii['out']='con'
          rx=ck.access(ii)
          if rx['return']>0: return rx

    elapsed_time=time.time()-start_time
    if o=='con':
       ck.out('Installation time: '+str(elapsed_time)+' sec.')

    return {'return':0, 'elapsed_time':elapsed_time}

##############################################################################
# setup package (only environment)

def setup(i):
    """
    Input:  {
               See 'install' function
               skip_process=yes
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    i['skip_process']='yes'
    return install(i)
